#! /usr/bin/env python3 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.api import webhooks, health, analytics
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="AI Code Reviewer",
    description="An intelligent code review assistant that uses AI to provide instant, actionable feedback on pull requests.",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])

@app.get("/")
async def root():
    return {"message": "AI Code Reviewer API",
            "docs": "/docs",
            "health": "/health"}