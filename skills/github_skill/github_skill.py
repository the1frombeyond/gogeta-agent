import subprocess


class GitHubSkill:
    name = "github"
    description = "GitHub CLI wrapper for repo management."

    def _run_gh(self, args):
        try:
            result = subprocess.run(["gh"] + args, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"GitHub CLI Error: {e.stderr}"
        except FileNotFoundError:
            return "GitHub CLI (gh) not found. Please install it from https://cli.github.com/"

    def run(self, command, context):
        # Example: pr checks
        if "pr checks" in command:
            # Simple parsing for demo; in real use, we'd use a more robust router
            args = command.split()
            return self._run_gh(args)

        # Default fallback
        return self._run_gh(command.split())

github_skill = GitHubSkill()
