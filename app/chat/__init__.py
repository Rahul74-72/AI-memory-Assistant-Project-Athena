from app.memory.memory import MemoryManager
from app.memory.memory_store import MemoryStore
from app.extractor.extractor import MemoryExtractor
from app.retrieval.retriever import MemoryRetriever


class ChatEngine:
    def __init__(self):
        self.memory = MemoryManager()
        self.memory_store = MemoryStore()
        self.extractor = MemoryExtractor()
        self.retriever = MemoryRetriever()
