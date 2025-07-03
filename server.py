"""SpaceX MCP Server - Model Context Protocol implementasyonu."""

import asyncio
import json
import sys
from typing import Any, Dict
from app import spacex_api, format_launch_data

class SpaceXMCPServer:
    """SpaceX MCP Server sınıfı."""
    
    def __init__(self):
        self.tools = [
            {
                "name": "get_latest_launch",
                "description": "SpaceX'in en son roket fırlatma bilgilerini alır",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_upcoming_launches", 
                "description": "SpaceX'in yaklaşan fırlatmalarını alır",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Kaç fırlatma bilgisi çekilecek (varsayılan: 5)",
                            "default": 5
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_company_info",
                "description": "SpaceX şirket bilgilerini alır", 
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """MCP request'lerini işler."""
        method = request.get("method")
        request_id = request.get("id")
        
        if method == "initialize":
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
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0", 
                "result": {"tools": self.tools},
                "id": request_id
            }
        
        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name == "get_latest_launch":
                data = spacex_api.get_latest_launch()
                if data:
                    formatted_text = format_launch_data(data)
                    return {
                        "jsonrpc": "2.0",
                        "result": {
                            "content": [{
                                "type": "text",
                                "text": formatted_text
                            }]
                        },
                        "id": request_id
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32000,
                            "message": "En son fırlatma verisi alınamadı"
                        },
                        "id": request_id
                    }
            
            elif tool_name == "get_upcoming_launches":
                limit = tool_args.get("limit", 5)
                data = spacex_api.get_upcoming_launches(limit)
                if data:
                    return {
                        "jsonrpc": "2.0",
                        "result": {
                            "content": [{
                                "type": "text", 
                                "text": json.dumps(data, indent=2, ensure_ascii=False)
                            }]
                        },
                        "id": request_id
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32000,
                            "message": "Yaklaşan fırlatma verileri alınamadı"
                        },
                        "id": request_id
                    }
            
            elif tool_name == "get_company_info":
                data = spacex_api.get_company_info()
                if data:
                    return {
                        "jsonrpc": "2.0",
                        "result": {
                            "content": [{
                                "type": "text",
                                "text": json.dumps(data, indent=2, ensure_ascii=False)
                            }]
                        },
                        "id": request_id
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32000,
                            "message": "Şirket bilgileri alınamadı"
                        },
                        "id": request_id
                    }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Bilinmeyen tool: {tool_name}"
                    },
                    "id": request_id
                }
        
        else:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Bilinmeyen method: {method}"
                },
                "id": request_id
            }

async def main():
    """Ana server fonksiyonu."""
    server = SpaceXMCPServer()
    
    # STDIO üzerinden MCP protokolü
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            request = json.loads(line.strip())
            response = await server.handle_request(request)
            
            print(json.dumps(response), flush=True)
            
        except (json.JSONDecodeError, KeyError) as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {e}"
                },
                "id": None
            }
            print(json.dumps(error_response), flush=True)
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0", 
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {e}"
                },
                "id": None
            }
            print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    asyncio.run(main())
