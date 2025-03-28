"""MCP server for deploying Modal applications."""
import logging
import os
from typing import Any, Optional, List, Dict, Union
import subprocess
import time
import json

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP("modal-deploy")

def run_modal_command(command: list[str], uv_directory: str = None) -> dict[str, Any]:
    """Run a Modal CLI command and return the result"""
    try:
        # uv_directory is necessary for modal deploy, since deploying the app requires the app to use the uv venv
        command = (["uv", "run", f"--directory={uv_directory}"] if uv_directory else []) + command
        logger.info(f"Running command: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return {
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": ' '.join(command)
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr,
            "command": ' '.join(command)
        }

def handle_json_response(result: Dict[str, Any], error_prefix: str) -> Dict[str, Any]:
    """
    Handle JSON parsing of command output and return a standardized response.
    
    Args:
        result: The result from run_modal_command
        error_prefix: Prefix to use in error messages
        
    Returns:
        A dictionary with standardized success/error format
    """
    if not result["success"]:
        response = {"success": False, "error": f"{error_prefix}: {result.get('error', 'Unknown error')}"}
        if result.get("stdout"):
            response["stdout"] = result["stdout"]
        if result.get("stderr"):
            response["stderr"] = result["stderr"]
        return response
    
    try:
        data = json.loads(result["stdout"])
        return {"success": True, "data": data}
    except json.JSONDecodeError as e:
        response = {"success": False, "error": f"Failed to parse JSON output: {str(e)}"}
        if result.get("stdout"):
            response["stdout"] = result["stdout"]
        if result.get("stderr"):
            response["stderr"] = result["stderr"]
        return response

@mcp.tool()
async def deploy_modal_app(absolute_path_to_app: str) -> dict[str, Any]:
    """
    Deploy a Modal application using the provided parameters.

    Args:
        absolute_path_to_app: The absolute path to the Modal application to deploy.

    Returns:
        A dictionary containing deployment results.

    Raises:
        Exception: If deployment fails for any reason.
    """
    uv_directory = os.path.dirname(absolute_path_to_app)
    app_name = os.path.basename(absolute_path_to_app)
    try:
        result = run_modal_command(["modal", "deploy", app_name], uv_directory)
        return result
    except Exception as e:
        logger.error(f"Failed to deploy Modal app: {e}")
        raise

@mcp.tool()
async def list_modal_volumes() -> dict[str, Any]:
    """
    List all Modal volumes using the Modal CLI with JSON output.

    Returns:
        A dictionary containing the parsed JSON output of the Modal volumes list.
    """
    try:
        result = run_modal_command(["modal", "volume", "list", "--json"])
        response = handle_json_response(result, "Failed to list volumes")
        if response["success"]:
            return {"success": True, "volumes": response["data"]}
        return response
    except Exception as e:
        logger.error(f"Failed to list Modal volumes: {e}")
        raise

@mcp.tool()
async def list_modal_volume_contents(volume_name: str, path: str = "/") -> dict[str, Any]:
    """
    List files and directories in a Modal volume.

    Args:
        volume_name: Name of the Modal volume to list contents from.
        path: Path within the volume to list contents from. Defaults to root ("/").

    Returns:
        A dictionary containing the parsed JSON output of the volume contents.
    """
    try:
        result = run_modal_command(["modal", "volume", "ls", "--json", volume_name, path])
        response = handle_json_response(result, "Failed to list volume contents")
        if response["success"]:
            return {"success": True, "contents": response["data"]}
        return response
    except Exception as e:
        logger.error(f"Failed to list Modal volume contents: {e}")
        raise

@mcp.tool()
async def copy_modal_volume_files(volume_name: str, paths: List[str]) -> dict[str, Any]:
    """
    Copy files within a Modal volume. Can copy a source file to a destination file
    or multiple source files to a destination directory.

    Args:
        volume_name: Name of the Modal volume to perform copy operation in.
        paths: List of paths for the copy operation. The last path is the destination,
              all others are sources. For example: ["source1.txt", "source2.txt", "dest_dir/"]

    Returns:
        A dictionary containing the result of the copy operation.

    Raises:
        Exception: If the copy operation fails for any reason.
    """
    if len(paths) < 2:
        return {
            "success": False,
            "error": "At least one source and one destination path are required"
        }

    try:
        result = run_modal_command(["modal", "volume", "cp", volume_name] + paths)
        response = {
            "success": result["success"],
            "command": result["command"]
        }
        
        if not result["success"]:
            response["error"] = f"Failed to copy files: {result.get('error', 'Unknown error')}"
        else:
            response["message"] = f"Successfully copied files in volume {volume_name}"
            
        if result.get("stdout"):
            response["stdout"] = result["stdout"]
        if result.get("stderr"):
            response["stderr"] = result["stderr"]
            
        return response
    except Exception as e:
        logger.error(f"Failed to copy files in Modal volume: {e}")
        raise

@mcp.tool()
async def remove_modal_volume_file(volume_name: str, remote_path: str, recursive: bool = False) -> dict[str, Any]:
    """
    Delete a file or directory from a Modal volume.

    Args:
        volume_name: Name of the Modal volume to delete from.
        remote_path: Path to the file or directory to delete.
        recursive: If True, delete directories recursively. Required for deleting directories.

    Returns:
        A dictionary containing the result of the delete operation.

    Raises:
        Exception: If the delete operation fails for any reason.
    """
    try:
        command = ["modal", "volume", "rm"]
        if recursive:
            command.append("-r")
        command.extend([volume_name, remote_path])
        
        result = run_modal_command(command)
        response = {
            "success": result["success"],
            "command": result["command"]
        }
        
        if not result["success"]:
            response["error"] = f"Failed to delete {remote_path}: {result.get('error', 'Unknown error')}"
        else:
            response["message"] = f"Successfully deleted {remote_path} from volume {volume_name}"
            
        if result.get("stdout"):
            response["stdout"] = result["stdout"]
        if result.get("stderr"):
            response["stderr"] = result["stderr"]
            
        return response
    except Exception as e:
        logger.error(f"Failed to delete from Modal volume: {e}")
        raise

@mcp.tool()
async def put_modal_volume_file(volume_name: str, local_path: str, remote_path: str = "/", force: bool = False) -> dict[str, Any]:
    """
    Upload a file or directory to a Modal volume.

    Args:
        volume_name: Name of the Modal volume to upload to.
        local_path: Path to the local file or directory to upload.
        remote_path: Path in the volume to upload to. Defaults to root ("/").
                    If ending with "/", it's treated as a directory and the file keeps its name.
        force: If True, overwrite existing files. Defaults to False.

    Returns:
        A dictionary containing the result of the upload operation.

    Raises:
        Exception: If the upload operation fails for any reason.
    """
    try:
        command = ["modal", "volume", "put"]
        if force:
            command.append("-f")
        command.extend([volume_name, local_path, remote_path])
        
        result = run_modal_command(command)
        response = {
            "success": result["success"],
            "command": result["command"]
        }
        
        if not result["success"]:
            response["error"] = f"Failed to upload {local_path}: {result.get('error', 'Unknown error')}"
        else:
            response["message"] = f"Successfully uploaded {local_path} to {volume_name}:{remote_path}"
            
        if result.get("stdout"):
            response["stdout"] = result["stdout"]
        if result.get("stderr"):
            response["stderr"] = result["stderr"]
            
        return response
    except Exception as e:
        logger.error(f"Failed to upload to Modal volume: {e}")
        raise

@mcp.tool()
async def get_modal_volume_file(volume_name: str, remote_path: str, local_destination: str = ".", force: bool = False) -> dict[str, Any]:
    """
    Download files from a Modal volume.

    Args:
        volume_name: Name of the Modal volume to download from.
        remote_path: Path to the file or directory in the volume to download.
        local_destination: Local path to save the downloaded file(s). Defaults to current directory.
                         Use "-" to write file contents to stdout.
        force: If True, overwrite existing files. Defaults to False.

    Returns:
        A dictionary containing the result of the download operation.

    Raises:
        Exception: If the download operation fails for any reason.
    """
    try:
        command = ["modal", "volume", "get"]
        if force:
            command.append("--force")
        command.extend([volume_name, remote_path, local_destination])
        
        result = run_modal_command(command)
        response = {
            "success": result["success"],
            "command": result["command"]
        }
        
        if not result["success"]:
            response["error"] = f"Failed to download {remote_path}: {result.get('error', 'Unknown error')}"
        else:
            response["message"] = f"Successfully downloaded {remote_path} from volume {volume_name}"
            
        if result.get("stdout"):
            response["stdout"] = result["stdout"]
        if result.get("stderr"):
            response["stderr"] = result["stderr"]
            
        return response
    except Exception as e:
        logger.error(f"Failed to download from Modal volume: {e}")
        raise

if __name__ == "__main__":
    mcp.run()
