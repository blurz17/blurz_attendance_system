import sys
import os

# Add server directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "server")))

from main import app

print("Registered Routes:")
for route in app.routes:
    # Handle APIRoute and Mount
    path = getattr(route, "path", None)
    methods = getattr(route, "methods", None)
    name = getattr(route, "name", None)
    if path:
        print(f"[{methods}] {path} -> {name}")
