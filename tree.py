#!/usr/bin/env python3
import os
import sys

def is_venv(name):
    """Check if directory is virtual environment"""
    venv_names = {'venv', 'env', '.venv', '.env', 'virtualenv', '__pycache__', '.git', 'node_modules'}
    return name.lower() in venv_names

def tree(path=".", prefix="", max_depth=3, current_depth=0):
    """Print directory tree without virtual environments"""
    if current_depth >= max_depth:
        return
    
    try:
        items = sorted([f for f in os.listdir(path) if not f.startswith('.') and not is_venv(f)])
    except PermissionError:
        return
    
    for i, item in enumerate(items):
        full_path = os.path.join(path, item)
        is_last = i == len(items) - 1
        
        print(f"{prefix}{'└── ' if is_last else '├── '}{item}")
        
        if os.path.isdir(full_path):
            extension = "    " if is_last else "│   "
            tree(full_path, prefix + extension, max_depth, current_depth + 1)

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"{os.path.basename(os.path.abspath(path))}/")
    tree(path)