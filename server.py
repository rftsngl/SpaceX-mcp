"""SpaceX MCP (Model Context Protocol) server implementation."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import base64
from urllib.parse import parse_qs, urlparse
import sys

# Disable HTTP server verbose logging
import logging
logging.getLogger("http.server").setLevel(logging.ERROR)

class MCPHandler(BaseHTTPRequestHandler):
    """HTTP server handler for SpaceX MCP (Model Context Protocol) implementation."""
    # Cached data - memory'de tutarak performans artırımı
    _cached_launch_data = None
    
    # Override log_message to reduce verbosity
    def log_message(self, format, *args):
        """Suppress most HTTP logs except errors"""
        if args[1] != '200':
            sys.stderr.write("%s - - [%s] %s\n" %
                           (self.address_string(),
                            self.log_date_time_string(),
                            format%args))

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
        """Smithery configuration'ını parse et - geliştirilmiş versiyon"""
        config = {}
        if not query_string:
            return config

        try:
            params = parse_qs(query_string)
            
            # Base64 encoded config parametresi (Smithery'nin ana yöntemi)
            if 'config' in params and params['config']:
                try:
                    encoded_config = params['config'][0]
                    # URL-safe base64 decode
                    encoded_config = encoded_config.replace('-', '+').replace('_', '/')
                    # Padding ekle
                    while len(encoded_config) % 4:
                        encoded_config += '='
                    decoded_bytes = base64.b64decode(encoded_config)
                    config = json.loads(decoded_bytes.decode('utf-8'))
                except (base64.binascii.Error, json.JSONDecodeError, UnicodeDecodeError) as e:
                    # Silent fail - no logging for config errors during tool discovery
                    pass

            # Direct query parameters (dot-notation için fallback)
            for key, values in params.items():
                if key != 'config' and values:
                    config[key] = values[0]

        except (ValueError, TypeError, UnicodeDecodeError):
            # Silent fail
            pass

        return config

    def _send(self, payload, status=200):
        """Response gönder - geliştirilmiş CORS ve headers"""
        try:
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
            self.send_header('X-Response-Time', '0ms')
            self.end_headers()
            
            if payload is not None:
                response_json = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
                self.wfile.write(response_json.encode('utf-8'))
        except (BrokenPipeError, ConnectionResetError):
            # Client disconnected - ignore
            pass

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

    def do_POST(self):
        """Handle POST requests for MCP protocol endpoints."""
        try:
            if not self.path.startswith('/mcp'):
                self._send({"error": "Not found"}, 404)
                return

            content_length = int(self.headers.get('Content-Length', 0))
            if content_length <= 0:
                self._send({"error": "No content"}, 400)
                return

            body = self.rfile.read(content_length)
            req = json.loads(body)
            method = req.get('method')
            request_id = req.get('id')

            # ULTRA HIZLI: tools/list için hiç config parse etme - Smithery timeout önleme
            if method == 'tools/list':
                self._send({
                    "jsonrpc": "2.0",
                    "result": {
                        "tools": [
                            {
                                "name": "get_latest_launch",
                                "description": "SpaceX'in en son roket fırlatma bilgilerini alır",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
                                }
                            }
                        ]
                    },
                    "id": request_id
                })
                return

            # Configuration parse et - sadece tools/list dışında
            config = {}
            parsed_url = urlparse(self.path)
            if parsed_url.query:
                config = self._parse_config(parsed_url.query)

            resp = self._handle_mcp_method(method, request_id, config)
            if resp is not None:
                self._send(resp)

        except json.JSONDecodeError:
            self._send({
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"},
                "id": None
            }, 400)
        except (OSError, ValueError, TypeError):
            self._send({
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": "Internal error"},
                "id": None
            }, 500)
        except Exception:  # pylint: disable=broad-except
            # Catch all to prevent server crash
            self._send({
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": "Internal error"},
                "id": None
            }, 500)

    def do_GET(self):
        """Handle GET requests for health check and MCP endpoints."""
        try:
            if self.path == '/':
                # Root endpoint - basit response
                self._send({"status": "ok", "server": "spacex-mcp"})
            elif self.path == '/health':
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
                    "endpoints": ["/", "/health", "/debug", "/mcp"],
                    "methods": ["GET", "POST", "OPTIONS"],
                    "cached_data": self._cached_launch_data is not None
                })
            elif self.path.startswith('/mcp'):
                # MCP endpoint için GET request - Smithery compatibility
                self._send({"message": "MCP endpoint - use POST for protocol requests"}, 405)
            else:
                self._send({"error": "Not found"}, 404)
        except Exception:  # pylint: disable=broad-except
            self._send({"error": "Internal server error"}, 500)

    def do_DELETE(self):
        """Handle DELETE requests for MCP endpoints."""
        try:
            if self.path.startswith('/mcp'):
                self._send({"message": "DELETE supported"})
            else:
                self._send({"error": "Not found"}, 404)
        except Exception:  # pylint: disable=broad-except
            self._send({"error": "Internal server error"}, 500)

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight."""
        try:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
            self.send_header('Access-Control-Max-Age', '86400')
            self.end_headers()
        except Exception:  # pylint: disable=broad-except
            pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Starting SpaceX MCP Server on port {port}...")
    
    try:
        server = HTTPServer(('0.0.0.0', port), MCPHandler)
        print(f"✅ Server successfully bound to 0.0.0.0:{port}")
        print("🌐 Server is ready to accept connections")
        print("📋 Available endpoints:")
        print("   - GET  /         - Root health check")
        print("   - GET  /health   - Health status")
        print("   - POST /mcp      - MCP protocol")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 48:
            print(f"❌ Port {port} is already in use")
        else:
            print(f"❌ Server error: {e}")
        exit(1)
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        exit(1)
