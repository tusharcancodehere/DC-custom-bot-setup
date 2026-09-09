import logging
import os
from aiohttp import web

logger = logging.getLogger(__name__)

async def health_handler(request: web.Request) -> web.Response:
    """Respond to health checks with HTTP 200 and a JSON status."""
    return web.json_response({"status": "ok"})

def create_health_app() -> web.Application:
    """Create the aiohttp web application with health check routes."""
    app = web.Application()
    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)
    return app

class HealthServer:
    """Lightweight HTTP server to satisfy Render Web Service port checks and monitoring."""

    def __init__(self, host: str = "0.0.0.0", port: int | None = None):
        self.host = host
        if port is not None:
            self.port = port
        else:
            try:
                self.port = int(os.getenv("PORT", "10000"))
            except (ValueError, TypeError):
                self.port = 10000
        self.runner: web.AppRunner | None = None
        self.site: web.TCPSite | None = None

    async def start(self) -> None:
        """Start the HTTP server on the configured host and port."""
        app = create_health_app()
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        logger.info(f"Health server listening on http://{self.host}:{self.port}")
        print(f"Health server listening on http://{self.host}:{self.port}")

    async def stop(self) -> None:
        """Gracefully stop the HTTP server and release port."""
        if self.runner is not None:
            logger.info("Stopping health server...")
            await self.runner.cleanup()
            self.runner = None
            self.site = None
