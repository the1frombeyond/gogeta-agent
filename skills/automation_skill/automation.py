import json
import os
import subprocess
import time

TASKS_FILE = os.path.expanduser('~/.gogeta/automation/tasks.json')


class TaskScheduler:

    def __init__(self):
        os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
        self._running = {}
        self._load()

    def _load(self):
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE) as f:
                self.tasks = json.load(f)
        else:
            self.tasks = {}
            self._save()

    def _save(self):
        with open(TASKS_FILE, 'w') as f:
            json.dump(self.tasks, f, indent=2)

    def _runner(self, name, command, interval):
        while name in self._running and not self._running[name]:
            try:
                subprocess.run(command, shell=True, timeout=interval * 60)
            except Exception:
                pass
            time.sleep(interval * 60)

    def schedule(self, name, command, interval_minutes):
        self.tasks[name] = {'command': command,
                            'interval': interval_minutes, 'paused': False}
        self._save()
        return {'status': 'scheduled', 'name': name}

    def list(self):
        return self.tasks

    def remove(self, name):
        if name in self._running:
            del self._running[name]
        return self.tasks.pop(name, None)

    def pause(self, name):
        if name in self.tasks:
            self.tasks[name]['paused'] = True
            self._save()
            return {'status': 'paused'}
        return {'error': 'Task not found'}

    def resume(self, name):
        if name in self.tasks:
            self.tasks[name]['paused'] = False
            self._save()
            return {'status': 'resumed'}
        return {'error': 'Task not found'}

    def status(self):
        return self.tasks


def run(action, **kwargs):
    ts = TaskScheduler()
    method = getattr(ts, action, None)
    if method:
        return method(**kwargs)
    return {'error': f'Unknown action: {action}'}
