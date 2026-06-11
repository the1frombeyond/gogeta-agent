import os

from config import SAFE_DIR
from skills.base import Skill


class FileManagerSkill(Skill):
    name = "file_manager"
    description = "Handles file operations safely"

    def run(self, input_data, context):
        input_data = input_data.lower()
        if "list" in input_data:
            files = os.listdir(SAFE_DIR)
            return f"Workspace contains: {', '.join(files) if files else 'no files'}."

        return "Unsupported file operation or I need more specific instructions, sir."
