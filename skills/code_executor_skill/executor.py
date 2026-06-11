import subprocess
import sys


class CodeExecutor:

    def execute_python(self, code):
        try:
            result = subprocess.run([sys.executable, '-c', code],
                                    capture_output=True, text=True, timeout=30)
            return {'stdout': result.stdout, 'stderr': result.stderr,
                    'returncode': result.returncode}
        except subprocess.TimeoutExpired:
            return {'error': 'Execution timed out'}
        except Exception as e:
            return {'error': str(e)}

    def execute_javascript(self, code):
        try:
            result = subprocess.run(['node', '-e', code],
                                    capture_output=True, text=True, timeout=30)
            return {'stdout': result.stdout, 'stderr': result.stderr,
                    'returncode': result.returncode}
        except FileNotFoundError:
            return {'error': 'Node.js not found'}
        except subprocess.TimeoutExpired:
            return {'error': 'Execution timed out'}

    def execute_shell(self, command):
        try:
            result = subprocess.run(command, shell=True,
                                    capture_output=True, text=True, timeout=30)
            return {'stdout': result.stdout, 'stderr': result.stderr,
                    'returncode': result.returncode}
        except subprocess.TimeoutExpired:
            return {'error': 'Execution timed out'}


def run(action, **kwargs):
    exe = CodeExecutor()
    method = getattr(exe, action, None)
    if method:
        return method(**kwargs)
    return {'error': f'Unknown action: {action}'}
