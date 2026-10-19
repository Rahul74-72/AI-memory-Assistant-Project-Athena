"""Explicit one-time downloads. Run from the project virtual environment."""
import subprocess
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

if __name__ == "__main__":
    os.environ["ATHENA_MODEL_DOWNLOADS"] = "1"
    subprocess.run(["ollama", "pull", "llama3.2:3b"], check=True)
    subprocess.run(["ollama", "create", "athena-local", "-f", str(ROOT/"models"/"Modelfile")], check=True)
    subprocess.run(["ollama", "pull", "moondream"], check=True)
    from app.embeddings.embedding_manager import EmbeddingManager
    from app.media import speech_model
    EmbeddingManager().create_embedding("Model setup")
    speech_model()
    print("Chat, vision, embeddings and local speech models are installed.")
