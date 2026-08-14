from app.memory.memory import MemoryManager
from app.memory.memory_store import MemoryStore
from app.extractor.extractor import MemoryExtractor
from app.retrieval.retriever import MemoryRetriever


class ChatEngine:

    def __init__(self):

        self.memory = MemoryManager()          # Conversation Log

        self.memory_store = MemoryStore()      # Long-term Memory

        self.extractor = MemoryExtractor()     # Memory Extractor

        self.retriever = MemoryRetriever()     # Memory Search