"""SpaceX MCP (Model Context Protocol) server implementation."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import base64
from urllib.parse import parse_qs

class MCPHandler(BaseHTTPRequestHandler):
    """HTTP server handler for SpaceX MCP (Model Context Protocol) implementation."""
    # Cached data - memory'de tutarak performans artırımı
    _cached_launch_data = None

    @classmethod
    def _load_launch_data(cls):
        """Launch data'yı memory'ye cache'le - lazy loading için sadece gerektiğinde çağrılır"""
        if cls._cached_launch_data is None:
            try:
                with open('mcp_latest_launch.json', encoding='utf-8') as f:
                    cls._cached_launch_data = json.load(f)
                print("✓ Launch data successfully loaded into cache")
            except FileNotFoundError:
                print("⚠ Warning: mcp_latest_launch.json not found")
                cls._cached_launch_data = {"error": "Data file not available"}
            except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
                print(f"⚠ Warning: Error loading launch data: {e}")
                cls._cached_launch_data = {"error": f"Data loading error: {str(e)}"}
        return cls._cached_launch_data

    def _parse_config(self, query_string):
        """Smithery configuration'ını parse et"""
        config = {}
        if query_string:
            params = parse_qs(query_string)

            # Base64 encoded config parametresi
            if 'config' in params and params['config']:
                try:
                    encoded_config = params['config'][0]
                    decoded_bytes = base64.b64decode(encoded_config)
                    config = json.loads(decoded_bytes.decode('utf-8'))
                except (base64.binascii.Error, json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"Config parse error: {e}")

            # Direct query parameters (dot-notation için)
            for key, values in params.items():
                if key != 'config' and values:
                    config[key] = values[0]

        return config

    def _send(self, payload, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Access-Control-Max-Age', '86400')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))

    def _handle_mcp_method(self, method, request_id, config):
        """Handle different MCP protocol methods."""
        if method == 'initialize':
            return {
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "spacex-mcp",
                        "version": "1.0.0"
                    }
                },
                "id": request_id
            }

        elif method == 'ping':
            return {
                "jsonrpc": "2.0",
                "result": {},
                "id": request_id
            }

        elif method == 'tools/list':
            # Smithery lazy loading - hiçbir I/O işlemi yapma, sadece tool listesini döndür
            # Bu metod çok hızlı response vermeli
            return {
                "jsonrpc": "2.0",
                "result": {
                    "tools": [{
                        "name": "get_latest_launch",
                        "description": "SpaceX'in en son roket fırlatma bilgilerini alır",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }]
                },
                "id": request_id
            }

        elif method == 'tools/call':
            # Sadece tools/call'da veri yükleme yap
            return self._handle_tools_call(request_id, config)

        elif method == 'notifications/initialized':
            return None  # Notification - response gerekmez

        else:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                },
                "id": request_id
            }

    def _handle_tools_call(self, request_id, config):
        """Handle tools/call method."""
        launch_data = self._load_launch_data()

        if isinstance(launch_data, dict) and "error" in launch_data:  # pylint: disable=unsupported-membership-test
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32000,
                    "message": launch_data["error"]  # pylint: disable=unsubscriptable-object
                },
                "id": request_id
            }

        # API key log (opsiyonel)
        if config.get('apiKey'):
            print(f"🔑 API Key: {config['apiKey'][:10]}...")

        return {
            "jsonrpc": "2.0",
            "result": {
                "content": [{
                    "type": "text",
                    "text": json.dumps(launch_data, indent=2)
                }]
            },
            "id": request_id
        }

    def do_POST(self):  # pylint: disable=invalid-name
        """Handle POST requests for MCP protocol endpoints."""
        if not self.path.startswith('/mcp'):
            self._send({"error": "Not found"}, 404)
            return

        # Configuration parse et - hızlı parse
        config = {}
        if '?' in self.path:
            query_string = self.path.split('?', 1)[1]
            config = self._parse_config(query_string)

        content_length = int(self.headers.get('Content-Length', 0))
        if content_length <= 0:
            self._send({"error": "No content"}, 400)
            return

        try:
            req = json.loads(self.rfile.read(content_length))
            method = req.get('method')
            request_id = req.get('id')

            # Smithery için hızlı response - sadece tools/list ve initialize için log
            if method in ['tools/list', 'initialize']:
                print(f"⚡ Fast response for: {method}")

            resp = self._handle_mcp_method(method, request_id, config)
            if resp is not None:
                self._send(resp)

        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            self._send({
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"},
                "id": None
            }, 400)
        except (OSError, ValueError, TypeError) as e:
            print(f"❌ Server Error: {e}")
            self._send({
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": "Internal error"},
                "id": None
            }, 500)

    def do_GET(self):  # pylint: disable=invalid-name
        """Handle GET requests for health check and MCP endpoints."""
        if self.path == '/health':
            # Health check - lazy loading için veri yükleme yapmıyoruz
            self._send({
                "status": "healthy", 
                "server": "spacex-mcp", 
                "cached": self._cached_launch_data is not None
            })
        elif self.path == '/debug':
            # Debug endpoint for troubleshooting
            self._send({
                "server": "spacex-mcp",
                "version": "1.0.0",
                "endpoints": ["/health", "/debug", "/mcp"],
                "methods": ["GET", "POST", "OPTIONS"],
                "cached_data": self._cached_launch_data is not None
            })
        elif self.path.startswith('/mcp'):
            self._send({"error": "Use POST for MCP protocol"}, 405)
        else:
            self._send({"error": "Not found"}, 404)

    def do_DELETE(self):  # pylint: disable=invalid-name
        """Handle DELETE requests for MCP endpoints."""
        if self.path.startswith('/mcp'):
            self._send({"message": "DELETE supported"})
        else:
            self._send({"error": "Not found"}, 404)

    def do_OPTIONS(self):  # pylint: disable=invalid-name
        """Handle OPTIONS requests for CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 SpaceX MCP Server starting on port {port}...")
    print("📋 Supported methods: initialize, ping, tools/list, tools/call")
    print(f"🌐 Server will be available at: http://0.0.0.0:{port}")
    print("✅ Ready to accept connections...")

    try:
        server = HTTPServer(('0.0.0.0', port), MCPHandler)
        print(f"✅ Server successfully bound to port {port}")
        print("🔗 Available endpoints:")
        print("   - GET  /health  - Health check")
        print("   - GET  /debug   - Debug info")
        print("   - POST /mcp     - MCP protocol")
        print("   - OPTIONS /mcp  - CORS preflight")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {port} is already in use. Please use a different port.")
        else:
            print(f"❌ Server failed to start: {e}")
        exit(1)
    except ValueError as e:
        print(f"❌ Server failed to start: {e}")
        exit(1)
