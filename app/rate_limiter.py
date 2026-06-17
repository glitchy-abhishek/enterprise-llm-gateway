import time
from redis.asyncio import Redis
from fastapi import HTTPException

# 1. Connect to the local Docker Redis container
redis_client = Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)

async def check_rate_limit(team_id: str, requests_per_minute: int):
    """
    Enforces a requests-per-minute limit using Redis.
    Creates a unique key for the current minute and increments it.
    """
    # Get the current time in minutes
    current_minute = int(time.time() // 60)
    
    # Create a unique database key for this team for this exact minute
    redis_key = f"rate_limit:{team_id}:{current_minute}"

    # Increment the counter (Redis does this atomically)
    current_requests = await redis_client.incr(redis_key)

    # If this is the very first request this minute, tell Redis to delete the key after 60 seconds
    # This prevents your database memory from filling up over time!
    if current_requests == 1:
        await redis_client.expire(redis_key, 60)

    # Block the request if they went over the YAML config limit
    if current_requests > requests_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded! Team '{team_id}' is allowed {requests_per_minute} requests per minute."
        )