"""SpaceX MCP (Model Context Protocol) server implementation."""

from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# Disable Flask logging
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/mcp', methods=['POST'])
def mcp_endpoint():
    """Handle MCP protocol requests."""
    try:
        data = request.get_json()
        method = data.get('method')
        request_id = data.get('id')
        
        # KRITIK: tools/list ANINDA dön
        if method == 'tools/list':
            return jsonify({
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
            })
        
        # Diğer method'lar
        if method == 'initialize':
            return jsonify({
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
            })
        
        elif method == 'ping':
            return jsonify({
                "jsonrpc": "2.0",
                "result": {},
                "id": request_id
            })
        
        elif method == 'tools/call':
            try:
                with open('mcp_latest_launch.json', 'r', encoding='utf-8') as f:
                    launch_data = json.load(f)
                return jsonify({
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": json.dumps(launch_data, indent=2)
                        }]
                    },
                    "id": request_id
                })
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": "Data not available"
                    },
                    "id": request_id
                })
        
        # Method not found
        return jsonify({
            "jsonrpc": "2.0",
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            },
            "id": request_id
        })
        
    except (KeyError, AttributeError, TypeError, ValueError):
        return jsonify({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": "Internal error"
            },
            "id": None
        }), 500

@app.route('/')
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    # Production mode için
    app.run(host='0.0.0.0', port=port, debug=False)
