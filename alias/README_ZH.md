runtime-sandbox-server --extension src/alias/runtime/alias_sandbox/alias_sandbox.py
python -m uvicorn alias.server.main:app --host 0.0.0.0 --port 8000 --reload
