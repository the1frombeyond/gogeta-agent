from config import NOTES_FILE
from skills.base import Skill


class NotesSkill(Skill):
    name = "notes"
    description = "Saves and reads notes"

    def run(self, input_data, context):
        if "read" in input_data.lower() or "what" in input_data.lower():
            if not NOTES_FILE.exists():
                return "You haven't taken any notes yet, sir."
            with open(NOTES_FILE) as f:
                return f"Here are your notes: {f.read()}"

        with open(NOTES_FILE, "a") as f:
            f.write(input_data + "\n")

        return "Note saved to your digital journal, sir."
