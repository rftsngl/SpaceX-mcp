#!/usr/bin/env python3
"""SpaceX MCP Server - Model Context Protocol implementasyonu."""

import json
import sys
import logging
from typing import Any, Dict, List, Optional

# Import our SpaceX API
from app import spacex_api, format_launch_data

# Disable logging to avoid interfering with MCP protocol
logging.basicConfig(level=logging.CRITICAL)

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
    
    def handle_initialize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize request'ini işler."""
        return {
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
            "id": request.get("id")
        }
    
    def handle_tools_list(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Tools/list request'ini işler."""
        return {
            "jsonrpc": "2.0",
            "result": {
                "tools": self.tools
            },
            "id": request.get("id")
        }
    
    def handle_tools_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Tools/call request'ini işler."""
        params = request.get("params", {})
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        request_id = request.get("id")
        
        try:
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
                
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Tool execution error: {str(e)}"
                },
                "id": request_id
            }
    
    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """MCP request'lerini yönlendirir."""
        method = request.get("method")
        
        if method == "initialize":
            return self.handle_initialize(request)
        elif method == "initialized":
            # initialized notification - response gönderme
            return None
        elif method == "tools/list":
            return self.handle_tools_list(request)
        elif method == "tools/call":
            return self.handle_tools_call(request)
        else:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Bilinmeyen method: {method}"
                },
                "id": request.get("id")
            }
    
    def send_response(self, response: Dict[str, Any]) -> None:
        """Response'u STDOUT'a yazar."""
        json.dump(response, sys.stdout, ensure_ascii=False)
        sys.stdout.write('\n')
        sys.stdout.flush()
    
    def run(self) -> None:
        """Ana server loop'u."""
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    response = self.handle_request(request)
                    
                    if response is not None:
                        self.send_response(response)
                        
                except json.JSONDecodeError as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        },
                        "id": None
                    }
                    self.send_response(error_response)
                    
                except Exception as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        },
                        "id": None
                    }
                    self.send_response(error_response)
                    
        except KeyboardInterrupt:
            pass
        except EOFError:
            pass

def main():
    """Ana fonksiyon."""
    server = SpaceXMCPServer()
    server.run()

if __name__ == "__main__":
    main()
