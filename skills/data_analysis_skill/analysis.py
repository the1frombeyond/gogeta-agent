import csv
import json


class DataAnalyzer:

    def __init__(self):
        self.data = []
        self.headers = []

    def load_csv(self, path):
        try:
            with open(path) as f:
                reader = csv.DictReader(f)
                self.headers = reader.fieldnames
                self.data = list(reader)
            return {'rows': len(self.data), 'columns': self.headers}
        except Exception as e:
            return {'error': str(e)}

    def load_json(self, path):
        try:
            with open(path) as f:
                self.data = json.load(f)
            if self.data:
                self.headers = list(self.data[0].keys())
            return {'rows': len(self.data), 'columns': self.headers}
        except Exception as e:
            return {'error': str(e)}

    def describe(self):
        if not self.data:
            return {'error': 'No data loaded'}
        return {'rows': len(self.data), 'columns': self.headers,
                'column_count': len(self.headers)}

    def filter(self, column, op, value):
        result = []
        for row in self.data:
            try:
                if op == '==' and row.get(column) == value:
                    result.append(row)
                elif op == '>' and float(row.get(column, 0)) > float(value):
                    result.append(row)
                elif op == '<' and float(row.get(column, 0)) < float(value):
                    result.append(row)
            except (ValueError, TypeError):
                pass
        return result

    def aggregate(self, group_by, agg_col, func):
        groups = {}
        for row in self.data:
            key = row.get(group_by)
            if key not in groups:
                groups[key] = []
            try:
                groups[key].append(float(row.get(agg_col, 0)))
            except (ValueError, TypeError):
                pass
        result = {}
        for key, vals in groups.items():
            if func == 'sum':
                result[key] = sum(vals)
            elif func == 'avg':
                result[key] = sum(vals) / len(vals) if vals else 0
            elif func == 'count':
                result[key] = len(vals)
            elif func == 'max':
                result[key] = max(vals) if vals else 0
            elif func == 'min':
                result[key] = min(vals) if vals else 0
        return result

    def to_chart(self, type):
        return {'error': 'Chart generation requires matplotlib'}


def run(action, **kwargs):
    da = DataAnalyzer()
    method = getattr(da, action, None)
    if method:
        return method(**kwargs)
    return {'error': f'Unknown action: {action}'}
