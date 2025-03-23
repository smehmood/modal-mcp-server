#!/usr/bin/env python3
"""
Test script for the Modal MCP server.
This script verifies that the MCP server and its tools work correctly.
"""

import unittest
import requests
import json
import sys
import time
import subprocess
import os
import signal
from typing import Dict, Any, Optional
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from mcp_client import ModalMCPClient


class TestModalMCPServer(unittest.TestCase):
    """Test case for the Modal MCP server."""
    
    server_process = None
    server_url = "http://localhost:8000"
    
    @classmethod
    def setUpClass(cls):
        """Start the MCP server before running the tests."""
        print("Starting Modal MCP server...")
        cls.server_process = subprocess.Popen(
            ["python", "mcp_server.py"],
            preexec_fn=os.setsid,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for the server to start
        max_retries = 30
        retry_interval = 1
        
        for _ in range(max_retries):
            try:
                response = requests.get(f"{cls.server_url}/docs")
                if response.status_code == 200:
                    print("Server started successfully")
                    return
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                time.sleep(retry_interval)
        
        # If we get here, server failed to start
        if cls.server_process:
            os.killpg(os.getpgid(cls.server_process.pid), signal.SIGTERM)
            stdout, stderr = cls.server_process.communicate()
            error_msg = f"Server failed to start after {max_retries} retries.\nStdout: {stdout}\nStderr: {stderr}"
            raise Exception(error_msg)
    
    def setUp(self):
        """Set up test cases."""
        self.client = ModalMCPClient(self.server_url)
    
    def test_schema_endpoint(self):
        """Test that the schema endpoint returns valid JSON."""
        response = requests.get(f"{self.server_url}/mcp/schema")
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        self.assertIsInstance(schema, dict)
        self.assertIn("tools", schema)
    
    def test_deploy_app(self):
        """Test deploying a Modal app."""
        # Create a temporary app file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import modal

stub = modal.Stub()

@stub.function()
def hello():
    return "Hello from Modal!"
            """)
            temp_path = f.name
        
        try:
            # Test deploying the app using the client
            result = self.client.deploy_app(temp_path)
            self.assertIn("status", result)
        finally:
            # Clean up
            os.unlink(temp_path)
    
    def test_run_function(self):
        """Test running a Modal function."""
        # Create a temporary app file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import modal

stub = modal.Stub()

@stub.function()
def hello(name="world"):
    return f"Hello, {name}!"
            """)
            temp_path = f.name
        
        try:
            # Test running the function using the client
            result = self.client.run_function(temp_path, "hello", name="test")
            self.assertIn("status", result)
        finally:
            # Clean up
            os.unlink(temp_path)
    
    @classmethod
    def tearDownClass(cls):
        """Stop the MCP server after running the tests."""
        if cls.server_process:
            print("Stopping Modal MCP server...")
            os.killpg(os.getpgid(cls.server_process.pid), signal.SIGTERM)
            cls.server_process.wait()
            print("Server stopped")


class TestModalMCPClientMock(unittest.TestCase):
    """Test the Modal MCP client with a mock server."""
    
    class MockModalMCPClient(ModalMCPClient):
        def __init__(self, server_url: str):
            self.server_url = server_url
            self.schema = {
                "schema_version": "v1",
                "name": "modal-tools",
                "tools": [
                    {
                        "name": "modal_deploy_app",
                        "description": "Deploy a Modal app"
                    },
                    {
                        "name": "modal_run",
                        "description": "Run a Modal function"
                    }
                ]
            }
            self.tools = self._init_tools()
        
        def _call_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
            return {"status": "success", "message": "Mocked response"}
    
    def setUp(self):
        """Set up test cases."""
        self.client = self.MockModalMCPClient("http://mock-server")
    
    def test_deploy_app(self):
        """Test deploying an app with the mocked client."""
        result = self.client.deploy_app("test_app.py")
        self.assertEqual(result["status"], "success")
    
    def test_run_function(self):
        """Test running a function with the mocked client."""
        result = self.client.run_function("test_app.py", "test_function")
        self.assertEqual(result["status"], "success")


if __name__ == '__main__':
    unittest.main() 