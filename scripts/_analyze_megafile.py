"""Analyze a megafile's structure -- classes, functions, imports."""
import ast
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(sys.argv[1], encoding='utf-8') as f:
    content = f.read()

tree = ast.parse(content)
lines = content.splitlines()

classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
top_funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]

print(f"File: {sys.argv[1]}")
print(f"Line count: {len(lines)}")
print(f"Classes: {len(classes)}")
print()

# Print imports
imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
for imp in imports:
    if isinstance(imp, ast.ImportFrom):
        module = imp.module or '.'
        names = ', '.join(a.name for a in imp.names)
        print(f"  from {module} import {names}")
    else:
        names = ', '.join(a.name for a in imp.names)
        print(f"  import {names}")

print()
print("Classes and their methods:")
for c in classes:
    methods = [n for n in ast.walk(c) if isinstance(n, ast.FunctionDef)]
    print(f"\n  {c.name} ({len(methods)} methods, line {c.lineno}-{c.end_lineno})")
    for m in methods:
        print(f"    {m.name} (line {m.lineno})")

print()
print("Top-level functions:")
for f in top_funcs:
    print(f"  {f.name} (line {f.lineno})")
