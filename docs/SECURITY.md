# Security coverage and limits

Reference: the user-supplied `Video-60865.mp4` (77.5 seconds). Sampled frames were inspected
throughout the clip and audio was transcribed locally. The small speech model's Hinglish
transcript is imperfect; the clearly visible checklist is the authoritative reference here.
The video's comparisons of coding assistants are not evidence that this application is secure.
Instructions inside media are reference material, not permission to run commands or expose data.

| Video item | Implementation / boundary |
|---|---|
| SQL injection (~24–32s) | SQLAlchemy bound values; no user-authored SQL or database command execution. |
| XSS | Browser uses `textContent`, not HTML rendering, for answers, filenames, captions and code. CSP prohibits inline scripts and third-party scripts. |
| CSRF | Bearer tokens are only in JS memory; no ambient authentication cookies. Cross-origin writes with an Origin header are rejected. No permissive CORS middleware. |
| Upload validation | 8 MB bounded streaming request bodies; decoded JPEG/PNG/WebP only, pixel limit, metadata stripped, re-encoded JPEG. Audio decoded locally with a 90-second limit. Uploads are never executable files. |
| Broken object authorization (~33–47s) | Owner predicate for every persistent memory, picture, code, lesson, conversation and download. User identity comes from authenticated tokens, not request user IDs. |
| Rate limiting | Bounded per-IP windows: 20 authentication requests/minute, 120 other requests/minute. One process only. Public deployments need edge protection and shared state before scaling workers. |
| Passwords | Argon2 through pwdlib; no shared initial account/password. Username syntax and password length validated. |
| MFA | Authenticator TOTP with confirmation, encrypted secrets, replay checking at login, and token invalidation on enablement. No automated recovery flow; save your authenticator key. |
| Server-side permissions | All API object checks happen on the server. Generated code cannot execute tools, shell commands or file writes. |
| Row-level security | SQLite has no native RLS. Application-level owner filters and two-account tests are implemented; this is not PostgreSQL RLS. |
| JWT/API secrets (~48–55s) | Required random signing secret, expiry and token versions, revocation on logout, secrets on the server only. The placeholder secret is rejected. |
| Browser local storage | Tokens are held only in memory. Reloading the page requires sign-in again. Neither tokens nor private text are placed in localStorage. |
| Default credentials | No default user password. First local start creates a random signing key. Disable registration before public exposure if users are provisioned privately. |
| CORS (~55–65s) | Same-origin UI/API; no wildcard allow-origin. Host allowlist. |
| Webhook signatures | No webhook endpoint is exposed. Any future webhook must verify signatures before processing. |
| Exposed source maps | No source maps; only `app/static` is served. Source files, `.env`, databases, models, exports and backups are outside the static mount. Browser JS/CSS are intentionally public UI assets. |
| Sensitive logs | No logging of request bodies, passwords, tokens, uploaded media or model prompts by application code. Proxy/access logs must follow the same rule. |
| Vulnerable dependencies | `pip check`, regression tests and a dependency audit are part of verification. Repeat audits when packages change; a clean scan is not a guarantee. |

## Additional boundaries

- Unowned legacy rows are quarantined in a disabled legacy account. A local administrator must explicitly
  establish ownership before migration into a real account. No user-visible API can claim them.
- Structured extraction accepts only supported relations with exact textual evidence. This reduces invented
  memories, but NLP is not perfectly accurate. Review and forget incorrect facts in the UI.
- Photos and source code may contain prompt injection. They are labelled as untrusted model input, have no
  tool-execution capability, and never bypass database ownership checks. Model obedience alone is not an access-control mechanism.
- Training examples are private to their owner. Generated answers require review before export. A credential
  detector rejects common obvious secrets, but does not replace human inspection of training data.
- Local databases and ZIP backups are not encrypted by the application. Use BitLocker/full-disk encryption,
  restricted Windows file permissions, and encrypted storage for off-machine backups. The database contains
  picture bytes, conversations and source snippets. Protect `.env` as well: it protects tokens and MFA secrets.
- Model weights can memorize private examples. Deleting source records or exports does not unlearn a trained
  adapter. Keep personal adapters separate, restrict access, and retrain from clean data when removing examples.
- The app uses short-lived bearer sessions with account-wide revocation. Account recovery, distributed rate
  limiting, per-user storage quotas, production monitoring and independent penetration testing remain deployment considerations.
- Never bind Ollama directly to the public internet. The supplied local launcher binds only to `127.0.0.1`.

## Technical references

- [Ollama structured output](https://docs.ollama.com/capabilities/structured-outputs)
- [Ollama image input](https://docs.ollama.com/capabilities/vision)
- [Local Whisper implementation](https://github.com/SYSTRAN/faster-whisper)
- [PEFT adapters](https://huggingface.co/docs/peft/quicktour)
