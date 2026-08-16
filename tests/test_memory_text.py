import unittest

from app.embeddings.memory_text import memory_to_text


class MemoryTextTests(unittest.TestCase):

    def test_uses_supplied_subject(self):
        result = memory_to_text("Athena", "likes", "Python")
        self.assertEqual(result, "Athena likes Python.")

    def test_empty_subject_falls_back_to_user(self):
        result = memory_to_text("", "goal", "learn AI")
        self.assertEqual(result, "User's goal is learn AI.")

    def test_unknown_relation_still_formats_cleanly(self):
        result = memory_to_text("User", "works_with", "Athena")
        self.assertEqual(result, "User works with Athena.")


if __name__ == "__main__":
    unittest.main()
