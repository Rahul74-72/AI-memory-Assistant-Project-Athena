from app.memory.memory import MemoryManager

memory = MemoryManager()
memory.delete_all()
memory.close()

print("Database cleared.")
