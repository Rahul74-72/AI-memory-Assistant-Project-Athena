import requests


class OllamaClient:

    def __init__(
        self,
        model="llama3.2:3b",
        host="http://localhost:11434"
    ):
        self.model = model
        self.host = host

    def generate(self, prompt):

        response = requests.post(
            f"{self.host}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        return data["response"].strip()