import httpx
from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
from prometheus_client import Counter

from app.config import gateway_config, settings
from app.providers.openai_prov import OpenAIProvider
from app.providers.anthropic_prov import AnthropicProvider
from app.rate_limiter import check_rate_limit

# 1. Create the router
router = APIRouter()

# 2. Initialize our providers
providers = {
    "openai": OpenAIProvider(api_key=settings.openai_api_key),
    "anthropic": AnthropicProvider(api_key=settings.anthropic_api_key)
}

# 3. Create the Prometheus Metric Tracker
GATEWAY_REQUESTS = Counter(
    "gateway_requests_total",
    "Total requests processed by the gateway",
    ["team_id", "model", "status_code"]
)

# 4. Security/Auth Dependency
def verify_team(team_id: str):
    """Checks if the team exists in our config.yaml"""
    for team in gateway_config.teams:
        if team.team_id == team_id:
            return team
    raise HTTPException(status_code=401, detail="Invalid Team ID. Access Denied.")

# 5. The Main Proxy Endpoint
@router.post("/v1/chat/completions")
async def chat_proxy(request: Request, x_team_id: str = Header(...)):
    # Verify the team
    team = verify_team(x_team_id)

    # Extract the payload early so we know what model they want for our metrics
    body = await request.json()
    model = body.get("model", "unknown")
    messages = body.get("messages", [])
    stream = body.get("stream", False)
    temperature = body.get("temperature", 0.7)

    # ENFORCE RATE LIMITS (Wrapped to catch the 429 for metrics)
    try:
        await check_rate_limit(team.team_id, team.rate_limits.requests_per_minute)
    except HTTPException as e:
        # Record the 429 Rate Limit error, then re-raise it
        GATEWAY_REQUESTS.labels(team_id=team.team_id, model=model, status_code="429").inc()
        raise e

    # Enforce YAML rules
    if model not in team.allowed_models:
        # Record the 403 Forbidden error
        GATEWAY_REQUESTS.labels(team_id=team.team_id, model=model, status_code="403").inc()
        raise HTTPException(
            status_code=403, 
            detail=f"Team '{team.team_id}' is not authorized to use model '{model}'"
        )

    # Route to the correct provider dynamically based on the model name
    if "gpt" in model:
        provider = providers["openai"]
    elif "claude" in model:
        provider = providers["anthropic"]
    else:
        GATEWAY_REQUESTS.labels(team_id=team.team_id, model=model, status_code="400").inc()
        raise HTTPException(status_code=400, detail="Routing for this model is not yet implemented.")

    # Execute the request safely using try/except
    try:
        if stream:
            response = StreamingResponse(
                provider.generate_stream(model=model, messages=messages, temperature=temperature),
                media_type="text/event-stream"
            )
            # Record a successful streaming request
            GATEWAY_REQUESTS.labels(team_id=team.team_id, model=model, status_code="200").inc()
            return response
        else:
            response = await provider.generate(model=model, messages=messages, temperature=temperature)
            # Record a successful standard request
            GATEWAY_REQUESTS.labels(team_id=team.team_id, model=model, status_code="200").inc()
            return response
            
    except httpx.HTTPStatusError as e:
        # Record upstream AI Provider Error (like 401 Bad Key)
        GATEWAY_REQUESTS.labels(team_id=team.team_id, model=model, status_code=str(e.response.status_code)).inc()
        raise HTTPException(
            status_code=e.response.status_code, 
            detail=f"Upstream AI Provider Error: {e.response.text}"
        )
    except Exception as e:
        # Record internal gateway crashes
        GATEWAY_REQUESTS.labels(team_id=team.team_id, model=model, status_code="500").inc()
        raise HTTPException(status_code=500, detail=f"Internal Gateway Error: {str(e)}")