
from contextlib import asynccontextmanager
from threading import Lock

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.chat.chat import ChatEngine


# Reuse the engine and serialize requests because the engine owns
# database sessions that are not request-scoped.
assistant = ChatEngine()
assistant_lock = Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        assistant.close()


app = FastAPI(
    title="Project Athena API",
    description="API for Athena's long-term AI memory assistant.",
    version="1.0.0",
    lifespan=lifespan,
)


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


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty or whitespace.",
        )

    try:
        with assistant_lock:
            result = assistant.process_message(message)

        return ChatResponse(**result)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        # Keep internal exception details out of the API response.
        raise HTTPException(
            status_code=500,
            detail="Athena could not process the message.",
        ) from exc
