"""
MCP Schema definition for Modal tools.
This file defines the schema for the tools that the MCP server provides.
"""

modal_tools_schema = {
    "schema_version": "v1",
    "name": "modal-tools",
    "description": "Tools for interacting with Modal, a platform for running serverless applications in the cloud",
    "tools": [
        {
            "name": "modal_deploy_app",
            "description": "Deploy a Modal application to the cloud",
            "input_schema": {
                "type": "object",
                "properties": {
                    "app_path": {
                        "type": "string",
                        "description": "Path to the Modal app file to deploy"
                    },
                    "app_name": {
                        "type": "string",
                        "description": "Custom name for the app (optional)"
                    }
                },
                "required": ["app_path"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Status of the deployment (success or error)"
                    },
                    "message": {
                        "type": "string",
                        "description": "Deployment message"
                    },
                    "details": {
                        "type": "string",
                        "description": "Detailed output from the deployment process"
                    }
                }
            }
        },
        {
            "name": "modal_run",
            "description": "Run a function in a Modal application",
            "input_schema": {
                "type": "object",
                "properties": {
                    "app_path": {
                        "type": "string",
                        "description": "Path to the Modal app file to run"
                    },
                    "function_name": {
                        "type": "string",
                        "description": "Name of the function to run"
                    },
                    "kwargs": {
                        "type": "object",
                        "description": "Command line arguments to pass to the function as --key value pairs",
                        "additionalProperties": {
                            "type": "string"
                        }
                    }
                },
                "required": ["app_path", "function_name"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Status of the run operation (success or error)"
                    },
                    "message": {
                        "type": "string",
                        "description": "Operation message"
                    },
                    "details": {
                        "type": "string",
                        "description": "Output from the function run"
                    }
                }
            }
        }
    ]
} 