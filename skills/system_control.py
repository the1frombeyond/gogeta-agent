import os

from skills.base import Skill


class SystemControlSkill(Skill):
    name = "system_control"
    description = "Controls system apps safely"

    def run(self, input_data, context):
        input_data = input_data.lower()
        if "open" in input_data:
            app = input_data.replace("open", "").strip()
            # Windows 'start' command
            os.system(f"start {app}")
            return f"Opened {app}, sir."

        return "No valid system command detected."
