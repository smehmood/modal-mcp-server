# Modal MCP Server

An MCP server implementation for interacting with Modal volumes and deploying Modal applications from within Cursor.

## Installation

1. Clone this repository:
```bash
git clone https://github.com/smehmood/modal-mcp-server.git
cd modal-mcp-server
```

2. Install dependencies using `uv`:
```bash
uv sync
```

## Configuration

To use this MCP server in Cursor, add the following configuration to your `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "modal-mcp-server": {
      "command": "uv",
      "args": [
        "--project", "/path/to/modal-mcp-server",
        "run", "/path/to/modal-mcp-server/src/modal_mcp/server.py"
      ]
    }
  }
}
```

Replace `/path/to/modal-mcp-server` with the absolute path to your cloned repository.

## Requirements

- Python 3.11 or higher
- `uv` package manager
- Modal CLI configured with valid credentials
- For Modal deploy support:
  - Project being deployed must use `uv` for dependency management
  - Modal must be installed in the project's virtual environment

## Supported Tools

### Modal Volume Operations

1. **List Modal Volumes** (`list_modal_volumes`)
   - Lists all Modal volumes in your environment
   - Returns JSON-formatted volume information
   - Parameters: None

2. **List Volume Contents** (`list_modal_volume_contents`)
   - Lists files and directories in a Modal volume
   - Parameters:
     - `volume_name`: Name of the Modal volume
     - `path`: Path within volume (default: "/")

3. **Copy Files** (`copy_modal_volume_files`)
   - Copies files within a Modal volume
   - Parameters:
     - `volume_name`: Name of the Modal volume
     - `paths`: List of paths where last path is destination
   - Example: `["source.txt", "dest.txt"]` or `["file1.txt", "file2.txt", "dest_dir/"]`

4. **Remove Files** (`remove_modal_volume_file`)
   - Deletes a file or directory from a Modal volume
   - Parameters:
     - `volume_name`: Name of the Modal volume
     - `remote_path`: Path to file/directory to delete
     - `recursive`: Boolean flag for recursive deletion (default: false)

5. **Upload Files** (`put_modal_volume_file`)
   - Uploads a file or directory to a Modal volume
   - Parameters:
     - `volume_name`: Name of the Modal volume
     - `local_path`: Path to local file/directory to upload
     - `remote_path`: Path in volume to upload to (default: "/")
     - `force`: Boolean flag to overwrite existing files (default: false)

6. **Download Files** (`get_modal_volume_file`)
   - Downloads files from a Modal volume
   - Parameters:
     - `volume_name`: Name of the Modal volume
     - `remote_path`: Path to file/directory in volume to download
     - `local_destination`: Local path to save downloaded files (default: current directory)
     - `force`: Boolean flag to overwrite existing files (default: false)
   - Note: Use "-" as `local_destination` to write file contents to stdout

### Modal Deployment

1. **Deploy Modal App** (`deploy_modal_app`)
   - Deploys a Modal application
   - Parameters:
     - `absolute_path_to_app`: Absolute path to the Modal application file
   - Note: The project containing the Modal app must:
     - Use `uv` for dependency management
     - Have the `modal` CLI installed in its virtual environment

## Response Format

All tools return responses in a standardized format:

```python
# Success case:
{
    "success": True,
    "message": "Operation successful message",  # For non-JSON operations
    "data": {...}  # For JSON operations (volumes/contents)
}

# Error case:
{
    "success": False,
    "error": "Error message describing what went wrong"
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.