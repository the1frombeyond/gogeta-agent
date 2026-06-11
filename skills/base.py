class Skill:
    name = "base"
    description = "Base skill template"

    def run(self, input_data: str, context: dict):
        raise NotImplementedError("Skill must implement run()")
