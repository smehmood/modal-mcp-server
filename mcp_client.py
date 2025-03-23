"""
MCP-compatible API client for Modal tools.
This client follows the Model Context Protocol standard to allow AI assistants
to interact with Modal through standardized tool calls.
"""

import json
import requests
from typing import Dict, List, Any, Optional, Callable


class ModalMCPClient:
    """MCP-compatible API client for Modal tools."""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        Initialize the Modal MCP API client.
        
        Args:
            server_url: URL of the Modal MCP server.
        """
        self.server_url = server_url.rstrip("/")
        self.schema = self._fetch_schema()
        self.tools = self._init_tools()
    
    def _fetch_schema(self) -> Dict[str, Any]:
        """Fetch the MCP schema from the server."""
        try:
            response = requests.get(f"{self.server_url}/mcp/schema")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Failed to fetch MCP schema from {self.server_url}: {e}")
    
    def _init_tools(self) -> Dict[str, Callable]:
        """Initialize the tools from the schema."""
        tools = {}
        
        for tool in self.schema.get("tools", []):
            tool_name = tool["name"]
            
            # Create a function for this tool
            def tool_func(tool_input: Dict[str, Any], _tool_name=tool_name) -> Dict[str, Any]:
                return self._call_tool(_tool_name, tool_input)
            
            # Add the documentation from the schema
            tool_func.__doc__ = tool["description"]
            
            # Add the function to the tools dictionary
            tools[tool_name] = tool_func
        
        return tools
    
    def _call_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call.
            tool_input: Input parameters for the tool.
            
        Returns:
            The result of the tool call.
        """
        url = f"{self.server_url}/mcp"
        payload = {
            "tool_name": tool_name,
            "tool_input": tool_input
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("error"):
                raise RuntimeError(f"Tool call error: {result['error']}")
            
            return result["tool_output"]
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error calling tool '{tool_name}': {e}"
            try:
                error_detail = response.json()
                error_msg += f"\nDetails: {json.dumps(error_detail)}"
            except:
                if response.text:
                    error_msg += f"\nResponse: {response.text}"
            raise RuntimeError(error_msg)
    
    def get_available_tools(self) -> List[str]:
        """
        Get a list of available tools.
        
        Returns:
            List of tool names.
        """
        return list(self.tools.keys())
    
    def get_tool_description(self, tool_name: str) -> str:
        """
        Get the description of a tool.
        
        Args:
            tool_name: Name of the tool.
            
        Returns:
            Description of the tool.
        """
        for tool in self.schema.get("tools", []):
            if tool["name"] == tool_name:
                return tool["description"]
        return "No description available."
    
    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """
        Get the schema of a tool.
        
        Args:
            tool_name: Name of the tool.
            
        Returns:
            Schema of the tool.
        """
        for tool in self.schema.get("tools", []):
            if tool["name"] == tool_name:
                return {
                    "input_schema": tool["input_schema"],
                    "output_schema": tool["output_schema"]
                }
        return {}
    
    # Define methods for each Modal tool
    def deploy_app(self, app_path: str, app_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Deploy a Modal application to the cloud.
        
        Args:
            app_path: Path to the Modal app file to deploy.
            app_name: Custom name for the app (optional).
            
        Returns:
            Result of the deployment operation.
        """
        tool_input = {"app_path": app_path}
        if app_name:
            tool_input["app_name"] = app_name
        return self.tools["modal_deploy_app"](tool_input)
    
    def run_function(self, app_path: str, function_name: str, **kwargs) -> Dict[str, Any]:
        """
        Run a Modal function.

        Args:
            app_path: Path to the Modal app file.
            function_name: Name of the function to run.
            **kwargs: Additional arguments to pass to the function.

        Returns:
            Dict containing the result of running the function.
        """
        tool_input = {
            "app_path": app_path,
            "function_name": function_name,
            "kwargs": kwargs
        }
        return self.tools["modal_run"](tool_input)


# Example of how an AI assistant might use this client
if __name__ == "__main__":
    # Create the MCP client
    client = ModalMCPClient()
    
    # Print available tools
    print("Available Modal tools:")
    for tool_name in client.get_available_tools():
        print(f"- {tool_name}: {client.get_tool_description(tool_name)}")
    
    # Example of using a tool via the MCP interface
    try:
        # An AI assistant would typically format their request like this
        tool_call = {
            "tool_name": "modal_run_app",
            "tool_input": {
                "app_path": "sample_app.py",
                "function_name": "hello",
                "args": ["AI Assistant"]
            }
        }
        
        # Execute the tool call
        result = client._call_tool(tool_call["tool_name"], tool_call["tool_input"])
        print("\nTool call result:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")