import os


class SystemMonitor:

    def __init__(self):
        self._psutil = None
        try:
            import psutil
            self._psutil = psutil
        except ImportError:
            pass

    def get_cpu(self):
        if self._psutil:
            return {'percent': self._psutil.cpu_percent(interval=0.1),
                    'count': self._psutil.cpu_count()}
        try:
            return {'percent': float(os.popen(
                "wmic cpu get loadpercentage").read().strip().split()[-1])}
        except Exception:
            return {'error': 'psutil not available'}

    def get_memory(self):
        if self._psutil:
            m = self._psutil.virtual_memory()
            return {'total': m.total, 'available': m.available,
                    'percent': m.percent, 'used': m.used}
        return {'error': 'psutil not available'}

    def get_disk(self):
        if self._psutil:
            return [{'device': d.device, 'mountpoint': d.mountpoint,
                     'fstype': d.fstype}
                    for d in self._psutil.disk_partitions()]
        return {'error': 'psutil not available'}

    def get_network(self):
        if self._psutil:
            n = self._psutil.net_io_counters()
            return {'bytes_sent': n.bytes_sent,
                    'bytes_recv': n.bytes_recv}
        return {'error': 'psutil not available'}

    def list_processes(self):
        if self._psutil:
            return [{'pid': p.info['pid'], 'name': p.info['name']}
                    for p in self._psutil.process_iter(['pid', 'name'])]
        return {'error': 'psutil not available'}

    def get_top_processes(self, n=5):
        if self._psutil:
            procs = []
            for p in self._psutil.process_iter(['pid', 'name',
                                                 'memory_percent']):
                try:
                    procs.append(p.info)
                except (self._psutil.NoSuchProcess,
                        self._psutil.AccessDenied):
                    pass
            procs.sort(key=lambda x: x.get('memory_percent', 0) or 0,
                       reverse=True)
            return procs[:n]
        return {'error': 'psutil not available'}


def run(action, **kwargs):
    mon = SystemMonitor()
    method = getattr(mon, action, None)
    if method:
        return method(**kwargs)
    return {'error': f'Unknown action: {action}'}
