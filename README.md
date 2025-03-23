# Modal MCP Server

This is a Model Context Protocol (MCP) server that provides tools for interacting with Modal, a platform for running serverless applications in the cloud. The server allows AI agents to deploy and run Modal apps.

## Features

The Modal MCP Server provides the following tools:

- **Deploy Modal Apps**: Deploy a Modal application to the cloud
- **Run Modal Functions**: Run a function in a Modal application

## Prerequisites

- Python 3.11 or higher
- Modal CLI installed and configured
- Modal account with API credentials

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/modal-mcp-server.git
   cd modal-mcp-server
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Log in to Modal using the CLI:
   ```
   modal token new
   ```

## Usage

### Starting the Server

Run the following command to start the MCP server:

```
python mcp_server.py
```

The server will start on `http://localhost:8000`.

### Accessing the API Documentation

Once the server is running, you can access the FastAPI documentation at:

```
http://localhost:8000/docs
```

### Integrating with MCP Clients

The server implements the Model Context Protocol (MCP), which allows AI agents to discover and use tools for interacting with Modal. To use this server with an MCP client, point the client to the MCP schema endpoint:

```
http://localhost:8000/mcp/schema
```

### Available Tools

#### 1. Deploy a Modal App

Deploys a Modal application to the cloud.

```
POST /mcp/tools/modal_deploy_app
```

**Request Body:**
```json
{
  "app_path": "path/to/your/app.py",
  "app_name": "my-app-name" // Optional
}
```

#### 2. Run a Modal Function

Runs a function in a Modal application.

```
POST /mcp/tools/modal_run
```

**Request Body:**
```json
{
  "app_path": "path/to/your/app.py",
  "function_name": "your_function_name",
  "kwargs": {"param1": "value1", "param2": "value2"} // Optional
}
```

## Example Usage with Python

Here's an example of how to use the Modal MCP Server from Python:

```python
import requests

# Deploy a Modal app
response = requests.post(
    "http://localhost:8000/mcp/tools/modal_deploy_app",
    json={
        "app_path": "my_app.py",
        "app_name": "my-deployed-app"
    }
)
print(response.json())

# Run a function in a Modal app
response = requests.post(
    "http://localhost:8000/mcp/tools/modal_run",
    json={
        "app_path": "my_app.py",
        "function_name": "process_data",
        "kwargs": {"output_format": "json"}
    }
)
print(response.json())
```

## License

[MIT License](LICENSE) 