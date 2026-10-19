from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.auth_routes import get_current_user
from app.chat.chat import ChatEngine
from app.database.models import User
from contextlib import asynccontextmanager
from pathlib import Path
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.auth_routes import router as auth_router, security_state
from app.workspace_routes import router as workspace_router
from app.database.database import Base, engine, get_db, DATABASE_PATH
from app.database.migrations import migrate_temporal_memory, migrate_multiuser_ownership
from app.auth import get_jwt_secret
from app.security import RequestSecurity
from app.database.models import TrainingExample
from app.learning import contains_secret
from app.llm.ollama_client import ModelUnavailable
from app.settings import CREATOR_NAME, PUBLIC_CLEARANCE_LEVELS
from sqlalchemy.orm import Session


@asynccontextmanager
async def lifespan(app):
    get_jwt_secret()  # Fail closed; never start a public service with a default secret.
    try:
        Base.metadata.create_all(bind=engine)
        migrate_temporal_memory(DATABASE_PATH)
        migrate_multiuser_ownership(DATABASE_PATH)
        yield
    finally:
        engine.dispose()


app = FastAPI(
    title="Project Athena API",
    description="API for Athena's long-term AI memory assistant.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None, redoc_url=None, openapi_url=None,
)
app.add_middleware(RequestSecurity)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=os.environ.get(
    "ATHENA_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver"
).split(","))
app.include_router(auth_router)
app.include_router(workspace_router)
STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC, check_dir=False), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC / "index.html")


@app.get("/manifest.webmanifest", include_in_schema=False)
def web_manifest():
    return FileResponse(STATIC / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/service-worker.js", include_in_schema=False)
def service_worker():
    return FileResponse(
        STATIC / "service-worker.js",
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/"},
    )


@app.exception_handler(ModelUnavailable)
async def model_unavailable(request, exc):
    return JSONResponse({"detail": str(exc)}, status_code=503)


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=5000,
        description="The message to send to Athena.",
    )


class ChatResponse(BaseModel):
    response: str
    memory_action: str | None = None


@app.get("/health")
def health():
    return {"status": "ok", "service": "Project Athena API"}


@app.get("/about")
def about():
    return {
        "name": "Project Athena",
        "creator": CREATOR_NAME,
        "maximum_clearance": PUBLIC_CLEARANCE_LEVELS[-1],
        "clearance_levels": PUBLIC_CLEARANCE_LEVELS,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty or whitespace.",
        )

    assistant = None

    try:
        assistant = ChatEngine(user_id=current_user.id)
        result = assistant.process_message(message)
        state = security_state(db, current_user.id)
        if state.auto_collect and not contains_secret(message+result["response"]):
            db.add(TrainingExample(user_id=current_user.id, prompt=message,
                                   answer=result["response"], approved=False))
        db.commit()
        return ChatResponse(**result)

    except ModelUnavailable:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Athena could not process the message.",
        ) from exc

    finally:
        if assistant is not None:
            assistant.close()
