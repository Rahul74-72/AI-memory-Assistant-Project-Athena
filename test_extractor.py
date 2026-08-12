from app.extractor.extractor import MemoryExtractor

extractor = MemoryExtractor()

tests = [
    "I live in Neemrana",
    "I like Python",
    "I love cricket",
    "I want to become an AI Engineer",
    "I am building an AI Memory Assistant",
    "Hello",
    "Thanks"
]

for text in tests:
    result = extractor.extract(text)
    print("\nInput:", text)
    print("Result:", result)
