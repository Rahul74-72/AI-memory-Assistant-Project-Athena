"""Request limits and TOTP support. Deployment uses one application worker."""
import base64
import hashlib
import hmac
import os
import struct
import time
from collections import OrderedDict, deque
from threading import Lock

from cryptography.fernet import Fernet
from starlette.responses import JSONResponse
from app.auth import get_jwt_secret
from app.settings import MAX_UPLOAD


def cipher():
    key = hashlib.sha256((get_jwt_secret()+":athena-totp-v1").encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def totp(secret, step):
    key = base64.b32decode(secret)
    digest = hmac.new(key, struct.pack(">Q", step), hashlib.sha1).digest()
    offset = digest[-1] & 15
    return f"{(struct.unpack('>I', digest[offset:offset+4])[0] & 0x7fffffff) % 1000000:06d}"


def verify_totp(encrypted, code, last_step=-1):
    if not code or len(code) != 6 or not code.isdigit():
        return None
    secret = cipher().decrypt(encrypted.encode()).decode()
    current = int(time.time()) // 30
    for step in (current, current-1, current+1):
        if step > last_step and hmac.compare_digest(totp(secret, step), code):
            return step
    return None


class RequestSecurity:
    """Bound streaming body size before multipart parsing; no request-body logging."""
    def __init__(self, app):
        self.app = app
        self.windows = OrderedDict()
        self.lock = Lock()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        path = scope["path"]
        origin = headers.get(b"origin", b"").decode()
        host = headers.get(b"host", b"").decode()
        if scope["method"] not in ("GET", "HEAD", "OPTIONS") and origin:
            if origin not in (f"http://{host}", f"https://{host}"):
                return await JSONResponse({"detail": "Cross-origin write rejected."}, 403)(scope, receive, send)
        if os.environ.get("ATHENA_RATE_LIMIT", "1") == "1":
            key = (scope.get("client", ("unknown",))[0], "auth" if path.startswith("/auth/") else "api")
            now = time.monotonic()
            with self.lock:
                queue = self.windows.setdefault(key, deque())
                while queue and queue[0] < now - 60:
                    queue.popleft()
                limited = len(queue) >= (20 if key[1] == "auth" else 120)
                if not limited:
                    queue.append(now)
                self.windows.move_to_end(key)
                if len(self.windows) > 10000:
                    self.windows.popitem(last=False)
            if limited:
                return await JSONResponse({"detail": "Too many requests. Try again shortly."}, 429,
                                          headers={"Retry-After": "60"})(scope, receive, send)
        # Buffer at most the upload limit, including chunked requests.
        chunks, total = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            total += len(chunk)
            if total > MAX_UPLOAD + 65536:
                return await JSONResponse({"detail": "Request exceeds 8 MB."}, 413)(scope, receive, send)
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        sent_body = False

        async def replay():
            nonlocal sent_body
            if not sent_body:
                sent_body = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()

        async def secure_send(message):
            if message["type"] == "http.response.start":
                message["headers"] += [
                    (b"x-content-type-options", b"nosniff"), (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"cache-control", b"no-store"),
                    (b"permissions-policy", b"camera=(), microphone=(self), geolocation=()"),
                    (b"content-security-policy", b"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; connect-src 'self'; media-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"),
                ]
                if scope["scheme"] == "https":
                    message["headers"].append((b"strict-transport-security", b"max-age=31536000"))
            await send(message)
        await self.app(scope, replay, secure_send)
