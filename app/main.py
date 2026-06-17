from fastapi import FastAPI
from prometheus_client import make_asgi_app # <-- New Import!
from app.config import settings, gateway_config
from app.router import router

app = FastAPI(
    title="Enterprise LLM Gateway",
    description="Centralized AI routing, rate limiting, and observability.",
    version="1.0.0"
)

# Attach the AI router
app.include_router(router)

# Mount the Prometheus metrics endpoint (New!)
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/health")
async def health_check():
    """Standard Kubernetes/Docker health probe endpoint."""
    return {
        "status": "healthy",
        "teams_loaded": len(gateway_config.teams),
        "providers_ready": ["OpenAI", "Anthropic"]
    }