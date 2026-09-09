import asyncio
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import aiohttp
from aiohttp import web
from core.health import HealthServer, create_health_app, health_handler

class TestHealthServer(unittest.IsolatedAsyncioTestCase):
    """Test suite for the lightweight HTTP health check server."""

    def test_create_health_app_routes(self):
        """Verify the health application registers GET / and GET /health."""
        app = create_health_app()
        routes = [
            (resource.canonical)
            for resource in app.router.resources()
        ]
        self.assertIn("/", routes)
        self.assertIn("/health", routes)

    async def test_health_handler_response(self):
        """Verify health_handler directly returns status 200 with JSON status: ok."""
        from aiohttp.test_utils import make_mocked_request
        request = make_mocked_request("GET", "/health")
        response = await health_handler(request)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.body, b'{"status": "ok"}')

    def test_health_server_port_configuration(self):
        """Verify HealthServer respects explicit ports and PORT env variable with fallback to 10000."""
        # Explicit port
        server = HealthServer(port=8080)
        self.assertEqual(server.port, 8080)
        self.assertEqual(server.host, "0.0.0.0")

        # PORT environment variable
        with patch.dict(os.environ, {"PORT": "9000"}):
            server_env = HealthServer()
            self.assertEqual(server_env.port, 9000)

        # Invalid PORT fallback to default 10000
        with patch.dict(os.environ, {"PORT": "not-a-number"}):
            server_invalid = HealthServer()
            self.assertEqual(server_invalid.port, 10000)

        # Unset PORT fallback to default 10000
        with patch.dict(os.environ, {}, clear=True):
            server_default = HealthServer()
            self.assertEqual(server_default.port, 10000)

    async def test_health_server_lifecycle_and_endpoints(self):
        """Verify server starts, responds to HTTP requests on / and /health with 200 OK, and stops."""
        # Use port 0 so the OS assigns a free ephemeral port for tests
        server = HealthServer(host="127.0.0.1", port=0)
        await server.start()

        # Retrieve actual assigned ephemeral port from site
        actual_port = None
        for socket in server.site._server.sockets:
            actual_port = socket.getsockname()[1]
            break
        self.assertIsNotNone(actual_port)

        base_url = f"http://127.0.0.1:{actual_port}"

        async with aiohttp.ClientSession() as session:
            # Test GET /
            async with session.get(f"{base_url}/") as resp:
                self.assertEqual(resp.status, 200)
                data = await resp.json()
                self.assertEqual(data, {"status": "ok"})

            # Test GET /health
            async with session.get(f"{base_url}/health") as resp:
                self.assertEqual(resp.status, 200)
                data = await resp.json()
                self.assertEqual(data, {"status": "ok"})

        # Stop server
        await server.stop()
        self.assertIsNone(server.runner)
        self.assertIsNone(server.site)

        # Idempotent stop test
        await server.stop()

if __name__ == "__main__":
    unittest.main()
