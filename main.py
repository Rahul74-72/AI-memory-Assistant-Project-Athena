from app.database.database import Base, engine
from app.database import models

from app.chat.chat import ChatEngine

Base.metadata.create_all(bind=engine)

assistant = ChatEngine()

assistant.chat()
