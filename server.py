from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class MCPHandler(BaseHTTPRequestHandler):
    def _send(self, payload):
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        method = req.get('method')
        if method == 'get_latest_launch':
            with open('mcp_latest_launch.json', encoding='utf-8') as f:
                result = json.load(f)
            resp = {"jsonrpc":"2.0","result":result,"id":req.get('id')}
        else:
            resp = {"jsonrpc":"2.0","error":{"code":-32601,"message":"Method not found"},"id":req.get('id')}
        self._send(resp)

if __name__=='__main__':
    HTTPServer(('',8080), MCPHandler).serve_forever()
