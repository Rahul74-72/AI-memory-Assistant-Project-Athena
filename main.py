from app.database.database import Base, engine
from app.database import models
from app.database.migrations import migrate_temporal_memory

from app.chat.chat import ChatEngine

Base.metadata.create_all(bind=engine)
migrate_temporal_memory()
assistant = ChatEngine()

assistant.chat()