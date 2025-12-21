"""
Shared HTTP Client for External Requests.

Provides a connection-pooled, timeout-configured HTTP client for
content fetching and API calls. Reuses connections for efficiency.
"""

import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager

import httpx

logger = logging.getLogger(__name__)

# Connection pool limits
MAX_CONNECTIONS = 100
MAX_CONNECTIONS_PER_HOST = 10
DEFAULT_TIMEOUT = 30.0  # seconds

# Global client instance (lazy initialization)
_http_client: Optional[httpx.AsyncClient] = None
_client_lock = asyncio.Lock()


async def get_http_client() -> httpx.AsyncClient:
    """
    Get or create the shared HTTP client.
    
    The client is created lazily on first use and reused for all requests.
    Connection pooling reduces overhead for repeated requests.
    
    Returns:
        Configured httpx.AsyncClient instance.
    """
    global _http_client
    
    async with _client_lock:
        if _http_client is None or _http_client.is_closed:
            _http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(DEFAULT_TIMEOUT),
                limits=httpx.Limits(
                    max_connections=MAX_CONNECTIONS,
                    max_keepalive_connections=MAX_CONNECTIONS_PER_HOST,
                ),
                headers={
                    "User-Agent": "Portfolio-Fit-Check-Agent/1.0",
                },
                follow_redirects=True,
            )
            logger.info(
                f"Shared HTTP client initialized: "
                f"max_connections={MAX_CONNECTIONS}, "
                f"timeout={DEFAULT_TIMEOUT}s"
            )
    
    return _http_client


async def close_http_client() -> None:
    """
    Close the shared HTTP client.
    
    Should be called during application shutdown.
    """
    global _http_client
    
    async with _client_lock:
        if _http_client is not None and not _http_client.is_closed:
            await _http_client.aclose()
            logger.info("Shared HTTP client closed")
            _http_client = None


@asynccontextmanager
async def get_client_session():
    """
    Context manager for using the shared HTTP client.
    
    Usage:
        async with get_client_session() as client:
            response = await client.get("https://example.com")
    """
    client = await get_http_client()
    yield client
