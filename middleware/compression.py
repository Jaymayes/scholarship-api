"""
Phase 4: Response Compression Middleware
Enables gzip compression for API responses
SEV-2 CIR-20260119-001: Performance Decompression
"""

import gzip
import io
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

COMPRESSIBLE_CONTENT_TYPES = {
    "application/json",
    "text/html",
    "text/plain",
    "text/css",
    "text/javascript",
    "application/javascript",
    "application/xml",
    "text/xml",
}

MIN_COMPRESS_SIZE = 500

EXCLUDED_PATHS = {
    "/health",
    "/healthz",
    "/readiness",
    "/metrics",
    "/",
}


class GZipMiddleware(BaseHTTPMiddleware):
    """
    GZip compression middleware for response bodies.
    
    Features:
    - Only compresses responses >500 bytes
    - Only compresses if client accepts gzip
    - Excludes health/metrics endpoints for fast probes
    - Sets proper Content-Encoding headers
    """
    
    def __init__(
        self,
        app,
        minimum_size: int = MIN_COMPRESS_SIZE,
        compression_level: int = 6,
        enabled: bool = True
    ):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compression_level = compression_level
        self.enabled = enabled
    
    def _should_compress(self, request: Request, response: Response) -> bool:
        """Determine if response should be compressed."""
        if not self.enabled:
            return False
        
        if request.url.path in EXCLUDED_PATHS:
            return False
        
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return False
        
        if response.headers.get("content-encoding"):
            return False
        
        content_type = response.headers.get("content-type", "")
        base_content_type = content_type.split(";")[0].strip()
        if base_content_type not in COMPRESSIBLE_CONTENT_TYPES:
            return False
        
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < self.minimum_size:
            return False
        
        return True
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        if not self._should_compress(request, response):
            return response
        
        if isinstance(response, StreamingResponse):
            body_chunks = []
            async for chunk in response.body_iterator:
                body_chunks.append(chunk if isinstance(chunk, bytes) else chunk.encode())
            body = b"".join(body_chunks)
        else:
            body = response.body
        
        if len(body) < self.minimum_size:
            return response
        
        buffer = io.BytesIO()
        with gzip.GzipFile(
            mode="wb",
            fileobj=buffer,
            compresslevel=self.compression_level
        ) as f:
            f.write(body)
        
        compressed_body = buffer.getvalue()
        
        if len(compressed_body) >= len(body):
            return response
        
        headers = dict(response.headers)
        headers["content-encoding"] = "gzip"
        headers["content-length"] = str(len(compressed_body))
        headers["vary"] = "Accept-Encoding"
        
        return Response(
            content=compressed_body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type
        )
