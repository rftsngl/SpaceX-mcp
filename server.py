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

    def do_GET(self):
        if self.path.startswith('/mcp'):
            # Tool listesi döndür (lazy loading için)
            tools = [
                {
                    "name": "get_latest_launch",
                    "description": "SpaceX'in en son roket fırlatma bilgilerini alır"
                }
            ]
            self._send({"tools": tools})
        else:
            self._send({"error": "Not found"}, 404)

    def do_POST(self):
        if self.path.startswith('/mcp'):
            # Configuration parametrelerini parse et
            query_params = {}
            if '?' in self.path:
                query_string = self.path.split('?', 1)[1]
                query_params = parse_qs(query_string)
            
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                req = json.loads(self.rfile.read(content_length))
                method = req.get('method')
                
                if method == 'get_latest_launch':
                    try:
                        with open('mcp_latest_launch.json', encoding='utf-8') as f:
                            result = json.load(f)
                        resp = {"jsonrpc": "2.0", "result": result, "id": req.get('id')}
                    except FileNotFoundError:
                        resp = {"jsonrpc": "2.0", "error": {"code": -32000, "message": "Data file not found"}, "id": req.get('id')}
                else:
                    resp = {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": req.get('id')}
                
                self._send(resp)
            else:
                self._send({"error": "No content"}, 400)
        else:
            self._send({"error": "Not found"}, 404)

    def do_DELETE(self):
        if self.path.startswith('/mcp'):
            self._send({"message": "DELETE işlemi desteklenmektedir"})
        else:
            self._send({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        self._send({})

if __name__ == '__main__':
    # PORT environment variable'ını kullan
    port = int(os.environ.get('PORT', 8080))
    print(f"Server {port} portunda başlatılıyor...")
    HTTPServer(('0.0.0.0', port), MCPHandler).serve_forever()
