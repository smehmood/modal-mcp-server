import os
import logging
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv
import modal
import traceback

from mcp_schema import modal_tools_schema

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Modal MCP Server")

# Modal client setup
try:
    modal_client = modal.Client(
        server_url=os.getenv("MODAL_SERVER_URL", "https://modal.com"),
        client_type="mcp-server",
        credentials=os.getenv("MODAL_TOKEN", "")
    )
    logger.info("Successfully connected to Modal")
except Exception as e:
    logger.error(f"Failed to connect to Modal: {e}")
    modal_client = None

# MCP Tool Models
class ModalDeployAppRequest(BaseModel):
    app_path: str = Field(..., description="Path to the Modal app file to deploy")
    app_name: Optional[str] = Field(None, description="Custom name for the app")

class ModalRunRequest(BaseModel):
    app_path: str
    function_name: str
    kwargs: Optional[Dict[str, str]] = None

class MCPRequest(BaseModel):
    tool_name: str
    tool_input: Dict[str, Any]

class MCPResponse(BaseModel):
    tool_name: str
    tool_output: Dict[str, Any]
    error: Optional[str] = None

# Helper Functions
def run_modal_command(command: List[str], background: bool = False) -> Dict[str, Any]:
    """Run a Modal CLI command and return the result"""
    import subprocess
    import time
    
    try:
        if background:
            # Run in background and don't wait for completion
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid  # Create new process group
            )
            # Give it a moment to start and check for immediate errors
            time.sleep(2)
            if process.poll() is not None:
                # Process ended early - there was an error
                _, stderr = process.communicate()
                return {
                    "success": False,
                    "error": "Process ended prematurely",
                    "stderr": stderr
                }
            return {
                "success": True,
                "message": "Process started successfully",
                "pid": process.pid
            }
        else:
            # Run normally and wait for completion
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            return {
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr
        }

# MCP Tool Implementations
@app.post("/mcp/tools/modal_deploy_app")
async def modal_deploy_app(request: ModalDeployAppRequest) -> Dict[str, Any]:
    """Deploy a Modal app"""
    try:
        command = ["modal", "deploy", request.app_path]
        if request.app_name:
            command.extend(["--name", request.app_name])
        
        result = run_modal_command(command)
        
        if result["success"]:
            return {
                "status": "success",
                "message": "App deployed successfully",
                "details": result["stdout"]
            }
        else:
            return {
                "status": "error",
                "message": "Failed to deploy app",
                "details": result["stderr"]
            }
    except Exception as e:
        logger.error(f"Error deploying Modal app: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/mcp/tools/modal_run")
async def modal_run(request: ModalRunRequest) -> Dict[str, Any]:
    """Run a Modal function."""
    try:
        cmd = ["modal", "run", f"{request.app_path}::{request.function_name}"]
        
        if request.kwargs:
            for key, value in request.kwargs.items():
                cmd.extend([f"--{key}", value])

        result = run_modal_command(cmd)
        return {
            "status": "success" if result["success"] else "error",
            "message": "Function executed successfully" if result["success"] else "Function execution failed",
            "details": result["stdout"] if result["success"] else result["stderr"]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to run Modal function: {str(e)}",
            "details": traceback.format_exc()
        }

# Standard MCP endpoints
@app.get("/mcp/schema")
async def mcp_schema():
    """Return the MCP schema for the Modal tools"""
    return modal_tools_schema

@app.post("/mcp/tools/{tool_name}")
async def mcp_tools_endpoint(tool_name: str, tool_input: Dict[str, Any]):
    """Generic endpoint for all MCP tools"""
    tool_handlers = {
        "modal_deploy_app": modal_deploy_app,
        "modal_run": modal_run
    }
    
    if tool_name not in tool_handlers:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    tool_model_classes = {
        "modal_deploy_app": ModalDeployAppRequest,
        "modal_run": ModalRunRequest
    }
    
    try:
        model_class = tool_model_classes[tool_name]
        tool_request = model_class(**tool_input)
        handler = tool_handlers[tool_name]
        result = await handler(tool_request)
        return result
    except Exception as e:
        logger.error(f"Error calling tool '{tool_name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Main MCP endpoint
@app.post("/mcp")
async def mcp_endpoint(request_data: Dict[str, Any], request: Request) -> Dict[str, Any]:
    """Main MCP endpoint that routes to the appropriate tool"""
    try:
        mcp_request = MCPRequest(**request_data)
        tool_name = mcp_request.tool_name
        tool_input = mcp_request.tool_input
        
        # Map tool names to handlers
        tool_handlers = {
            "modal_deploy_app": modal_deploy_app,
            "modal_run": modal_run
        }
        
        if tool_name not in tool_handlers:
            return MCPResponse(
                tool_name=tool_name,
                tool_output={},
                error=f"Unknown tool: {tool_name}"
            ).dict()
        
        # Create the appropriate request model and call the handler
        tool_model_classes = {
            "modal_deploy_app": ModalDeployAppRequest,
            "modal_run": ModalRunRequest
        }
        
        model_class = tool_model_classes[tool_name]
        tool_request = model_class(**tool_input)
        handler = tool_handlers[tool_name]
        result = await handler(tool_request)
        
        return MCPResponse(
            tool_name=tool_name,
            tool_output=result,
            error=None
        ).dict()
        
    except Exception as e:
        logger.error(f"Error processing MCP request: {e}")
        return MCPResponse(
            tool_name=request_data.get("tool_name", "unknown"),
            tool_output={},
            error=str(e)
        ).dict()

# Server startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Modal MCP Server")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Modal MCP Server")

if __name__ == "__main__":
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=8000, reload=True) 