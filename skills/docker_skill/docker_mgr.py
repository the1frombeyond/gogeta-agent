import subprocess


class DockerManager:

    def _run(self, args):
        try:
            result = subprocess.run(['docker'] + args,
                                    capture_output=True, text=True,
                                    timeout=60)
            if result.returncode != 0:
                return {'error': result.stderr.strip()}
            return {'output': result.stdout.strip()}
        except FileNotFoundError:
            return {'error': 'Docker not found'}
        except subprocess.TimeoutExpired:
            return {'error': 'Command timed out'}

    def list_containers(self, all=False):
        args = ['ps'] + (['-a'] if all else [])
        return self._run(args)

    def start(self, name):
        return self._run(['start', name])

    def stop(self, name):
        return self._run(['stop', name])

    def logs(self, name, lines=50):
        return self._run(['logs', '--tail', str(lines), name])

    def list_images(self):
        return self._run(['images', '--format',
                          '{{.Repository}}:{{.Tag}}'])

    def compose_up(self, file):
        return self._run(['compose', '-f', file, 'up', '-d'])

    def prune(self):
        return self._run(['system', 'prune', '-f'])


def run(action, **kwargs):
    dm = DockerManager()
    method = getattr(dm, action, None)
    if method:
        return method(**kwargs)
    return {'error': f'Unknown action: {action}'}
