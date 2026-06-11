import csv
import json
import sqlite3


class DatabaseManager:

    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self, path):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        return {'connected': True, 'path': path}

    def query(self, sql, params=None):
        if not self.conn:
            return {'error': 'Not connected to database'}
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            if sql.strip().upper().startswith(
                    ('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP')):
                self.conn.commit()
                return {'affected': self.cursor.rowcount}
            rows = [dict(r) for r in self.cursor.fetchall()]
            cols = [d[0] for d in self.cursor.description]
            return {'rows': rows, 'columns': cols}
        except Exception as e:
            return {'error': str(e)}

    def create_table(self, name, columns):
        cols = ', '.join(f'{c["name"]} {c["type"]}' for c in columns)
        return self.query(f'CREATE TABLE IF NOT EXISTS {name} ({cols})')

    def insert(self, table, data):
        cols = ', '.join(data.keys())
        placeholders = ', '.join('?' for _ in data)
        return self.query(f'INSERT INTO {table} ({cols}) VALUES '
                          f'({placeholders})', list(data.values()))

    def update(self, table, data, where):
        sets = ', '.join(f'{k}=?' for k in data)
        return self.query(f'UPDATE {table} SET {sets} WHERE {where}',
                          list(data.values()))

    def delete(self, table, where):
        return self.query(f'DELETE FROM {table} WHERE {where}')

    def export_csv(self, table, path):
        result = self.query(f'SELECT * FROM {table}')
        if 'error' in result:
            return result
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(result['columns'])
            writer.writerows([list(r.values()) for r in result['rows']])
        return {'exported': path, 'rows': len(result['rows'])}

    def export_json(self, table, path):
        result = self.query(f'SELECT * FROM {table}')
        if 'error' in result:
            return result
        with open(path, 'w') as f:
            json.dump(result['rows'], f, indent=2)
        return {'exported': path, 'rows': len(result['rows'])}


def run(action, **kwargs):
    db = DatabaseManager()
    method = getattr(db, action, None)
    if method:
        return method(**kwargs)
    return {'error': f'Unknown action: {action}'}
