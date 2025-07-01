from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import base64
from urllib.parse import parse_qs, urlparse

class MCPHandler(BaseHTTPRequestHandler):
    # Cached data - memory'de tutarak performans artırımı
    _cached_launch_data = None
    _startup_checked = False
    
    @classmethod
    def _load_launch_data(cls):
        """Launch data'yı memory'ye cache'le"""
        if cls._cached_launch_data is None:
            try:
                with open('mcp_latest_launch.json', encoding='utf-8') as f:
                    cls._cached_launch_data = json.load(f)
                print("✓ Launch data successfully loaded into cache")
            except FileNotFoundError:
                print("⚠ Warning: mcp_latest_launch.json not found")
                cls._cached_launch_data = {"error": "Data file not available"}
            except Exception as e:
                print(f"⚠ Warning: Error loading launch data: {e}")
                cls._cached_launch_data = {"error": f"Data loading error: {str(e)}"}
        return cls._cached_launch_data

    @classmethod
    def _startup_check(cls):
        """Server startup sırasında bir kere kontrol et"""
        if not cls._startup_checked:
            cls._load_launch_data()
            cls._startup_checked = True

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
                except Exception as e:
                    print(f"Config parse error: {e}")
            
            # Direct query parameters (dot-notation için)
            for key, values in params.items():
                if key != 'config' and values:
                    config[key] = values[0]
        
        return config

    def _send(self, payload, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_POST(self):
        if self.path.startswith('/mcp'):
            # Startup check
            self._startup_check()
            
            # Configuration parse et
            config = {}
            if '?' in self.path:
                query_string = self.path.split('?', 1)[1]
                config = self._parse_config(query_string)
            
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                try:
                    req = json.loads(self.rfile.read(content_length))
                    method = req.get('method')
                    request_id = req.get('id')
                    
                    print(f"📝 Method: {method}, Config: {config}")
                    
                    # MCP Protocol Methods
                    if method == 'initialize':
                        resp = {
                            "jsonrpc": "2.0",
                            "result": {
                                "protocolVersion": "2024-11-05",
                                "capabilities": {
                                    "tools": {}
                                },
                                "serverInfo": {
                                    "name": "spacex-mcp",
                                    "version": "1.0.0"
                                }
                            },
                            "id": request_id
                        }
                    
                    elif method == 'ping':
                        resp = {
                            "jsonrpc": "2.0",
                            "result": {},
                            "id": request_id
                        }
                    
                    elif method == 'tools/list':
                        # Lazy loading - authentication gerektirmez
                        tools = [
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
                        resp = {
                            "jsonrpc": "2.0",
                            "result": {
                                "tools": tools
                            },
                            "id": request_id
                        }
                    
                    elif method == 'tools/call':
                        params = req.get('params', {})
                        tool_name = params.get('name')
                        
                        if tool_name == 'get_latest_launch':
                            # Cached data kullan - çok daha hızlı
                            launch_data = self._load_launch_data()
                            
                            if "error" in launch_data:
                                resp = {
                                    "jsonrpc": "2.0",
                                    "error": {
                                        "code": -32000,
                                        "message": launch_data["error"]
                                    },
                                    "id": request_id
                                }
                            else:
                                # API key log (opsiyonel)
                                if config.get('apiKey'):
                                    print(f"🔑 API Key: {config['apiKey'][:10]}...")
                                
                                resp = {
                                    "jsonrpc": "2.0",
                                    "result": {
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": json.dumps(launch_data, indent=2)
                                            }
                                        ]
                                    },
                                    "id": request_id
                                }
                        else:
                            resp = {
                                "jsonrpc": "2.0",
                                "error": {
                                    "code": -32601,
                                    "message": f"Tool not found: {tool_name}"
                                },
                                "id": request_id
                            }
                    
                    elif method == 'notifications/initialized':
                        # Notification - response gerekmez
                        return
                    
                    else:
                        resp = {
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32601,
                                "message": f"Method not found: {method}"
                            },
                            "id": request_id
                        }
                    
                    self._send(resp)
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON Parse Error: {e}")
                    resp = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        },
                        "id": None
                    }
                    self._send(resp, 400)
                except Exception as e:
                    print(f"❌ Server Error: {e}")
                    resp = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": "Internal error"
                        },
                        "id": None
                    }
                    self._send(resp, 500)
            else:
                self._send({"error": "No content"}, 400)
        else:
            self._send({"error": "Not found"}, 404)

    def do_GET(self):
        if self.path == '/health':
            self._startup_check()
            status = "healthy" if self._cached_launch_data and "error" not in self._cached_launch_data else "degraded"
            self._send({
                "status": status, 
                "server": "spacex-mcp",
                "cached": self._cached_launch_data is not None
            })
        elif self.path.startswith('/mcp'):
            self._send({"error": "Use POST for MCP protocol"}, 405)
        else:
            self._send({"error": "Not found"}, 404)

    def do_DELETE(self):
        if self.path.startswith('/mcp'):
            self._send({"message": "DELETE supported"})
        else:
            self._send({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 SpaceX MCP Server starting on port {port}...")
    print("📋 Supported methods: initialize, ping, tools/list, tools/call")
    
    # Startup check
    MCPHandler._startup_check()
    
    try:
        HTTPServer(('0.0.0.0', port), MCPHandler).serve_forever()
    except KeyboardInterrupt:
        print("\n�� Server stopped")
