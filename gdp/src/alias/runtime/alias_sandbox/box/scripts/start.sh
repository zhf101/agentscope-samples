#!/bin/bash

# Start FastAPI app inside container; supervisord manages this script.
uvicorn app:app --app-dir=/agentscope_runtime --host=0.0.0.0 --port 8000 &
wait
