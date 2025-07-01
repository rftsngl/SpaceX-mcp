from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from urllib.parse import parse_qs, urlparse

class MCPHandler(BaseHTTPRequestHandler):
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
            # Configuration parametrelerini parse et
            query_params = {}
            if '?' in self.path:
                query_string = self.path.split('?', 1)[1]
                query_params = parse_qs(query_string)
            
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                try:
                    req = json.loads(self.rfile.read(content_length))
                    method = req.get('method')
                    request_id = req.get('id')
                    
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
                        # Ping metodunu ekle - bağlantı testi için gerekli
                        resp = {
                            "jsonrpc": "2.0",
                            "result": {},
                            "id": request_id
                        }
                    
                    elif method == 'tools/list':
                        # Tool listesi döndür (lazy loading - authentication gerektirmez)
                        # Kullanıcılar authentication olmadan araçları keşfedebilir
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
                        # Tool çağrısını işle
                        # Burada authentication kontrolü yapılabilir (sadece çağrı sırasında)
                        params = req.get('params', {})
                        tool_name = params.get('name')
                        
                        if tool_name == 'get_latest_launch':
                            try:
                                # Configuration'dan API key kontrolü (isteğe bağlı)
                                api_key = None
                                for key, value in query_params.items():
                                    if key == 'apiKey' and value:
                                        api_key = value[0]
                                
                                # API key varsa kullan, yoksa da devam et (lazy loading prensibi)
                                if api_key:
                                    print(f"API Key kullanılıyor: {api_key[:10]}...")
                                
                                with open('mcp_latest_launch.json', encoding='utf-8') as f:
                                    result = json.load(f)
                                
                                resp = {
                                    "jsonrpc": "2.0",
                                    "result": {
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": json.dumps(result, indent=2)
                                            }
                                        ]
                                    },
                                    "id": request_id
                                }
                            except FileNotFoundError:
                                resp = {
                                    "jsonrpc": "2.0",
                                    "error": {
                                        "code": -32000,
                                        "message": "Data file not found"
                                    },
                                    "id": request_id
                                }
                            except Exception as e:
                                resp = {
                                    "jsonrpc": "2.0",
                                    "error": {
                                        "code": -32000,
                                        "message": f"Internal error: {str(e)}"
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
                        # Notification handling - response gerekmez
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
                    
                except json.JSONDecodeError:
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
                    resp = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        },
                        "id": None
                    }
                    self._send(resp, 500)
            else:
                self._send({"error": "No content"}, 400)
        else:
            self._send({"error": "Not found"}, 404)

    def do_GET(self):
        # Health check için
        if self.path == '/health':
            self._send({"status": "healthy", "server": "spacex-mcp"})
        elif self.path.startswith('/mcp'):
            # MCP için sadece POST desteklenir
            self._send({"error": "Use POST for MCP protocol"}, 405)
        else:
            self._send({"error": "Not found"}, 404)

    def do_DELETE(self):
        if self.path.startswith('/mcp'):
            self._send({"message": "DELETE desteklenmektedir"})
        else:
            self._send({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == '__main__':
    # PORT environment variable'ını kullan
    port = int(os.environ.get('PORT', 8080))
    print(f"SpaceX MCP Server {port} portunda başlatılıyor...")
    print("Desteklenen metodlar: initialize, ping, tools/list, tools/call")
    HTTPServer(('0.0.0.0', port), MCPHandler).serve_forever()
