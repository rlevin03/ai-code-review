from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import webhooks, health, analytics
from app.config import settings

app = FastAPI(title="AI Code Reviewer")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

@app.get("/")
def root():
    return {"message": "AI Code Reviewer API"}