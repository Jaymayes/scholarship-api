"""
Forwarded Headers Middleware for proxy environments
Safely handles X-Forwarded-* headers from trusted proxies
"""

import ipaddress

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from config.settings import settings


class ForwardedHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to safely process forwarded headers from trusted proxies
    Essential for production deployments behind load balancers/reverse proxies
    """

    def __init__(self, app, trusted_proxies: list[str] = None):
        super().__init__(app)
        self.trusted_proxies = trusted_proxies or settings.trusted_proxy_ips
        self.trusted_networks = []

        # Parse trusted proxy IP ranges
        for proxy_ip in self.trusted_proxies:
            try:
                self.trusted_networks.append(ipaddress.ip_network(proxy_ip, strict=False))
            except ValueError:
                # Log warning but don't fail startup
                import logging
                logging.warning(f"Invalid trusted proxy IP/CIDR: {proxy_ip}")

    def _is_trusted_proxy(self, client_ip: str) -> bool:
        """Check if client IP is in trusted proxy list"""
        if not self.trusted_networks:
            return False

        try:
            client_addr = ipaddress.ip_address(client_ip)
            return any(client_addr in network for network in self.trusted_networks)
        except ValueError:
            return False

    async def dispatch(self, request: Request, call_next):
        """Process forwarded headers from trusted proxies"""

        # Get immediate client IP
        client_ip = request.client.host if request.client else None

        # Only process forwarded headers from trusted proxies
        if client_ip and self._is_trusted_proxy(client_ip):
            # Process X-Forwarded-For header
            forwarded_for = request.headers.get("x-forwarded-for")
            if forwarded_for:
                # Get the first (leftmost) IP which is the original client
                original_client = forwarded_for.split(",")[0].strip()
                # Update request state with real client IP
                request.state.real_client_ip = original_client

            # Process X-Forwarded-Proto header
            forwarded_proto = request.headers.get("x-forwarded-proto")
            if forwarded_proto:
                request.state.real_scheme = forwarded_proto.strip().lower()

            # Process X-Forwarded-Host header
            forwarded_host = request.headers.get("x-forwarded-host")
            if forwarded_host:
                request.state.real_host = forwarded_host.strip()
        else:
            # Not from trusted proxy, use direct connection info
            request.state.real_client_ip = client_ip
            request.state.real_scheme = request.url.scheme
            request.state.real_host = request.headers.get("host", "")

        return await call_next(request)
