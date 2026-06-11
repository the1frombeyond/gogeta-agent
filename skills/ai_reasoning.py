import requests

from skills.base import Skill


class AIReasoningSkill(Skill):
    name = "ai_reasoning"
    description = "Uses Ollama for reasoning tasks"

    def run(self, input_data, context):
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3",
                    "prompt": input_data,
                    "stream": False
                },
                timeout=30
            )
            return response.json().get("response", "I encountered an error while reasoning.")
        except Exception as e:
            return f"Ollama Error: {e}"
