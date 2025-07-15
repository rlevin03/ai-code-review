#!/bin/bash
echo "Starting FastAPI server..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000 &
SERVER_PID=$!

echo "Waiting for server to start..."
sleep 3

echo "Starting ngrok..."
ngrok http 8000