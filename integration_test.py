import os
import signal
import subprocess
import time
from typing import Optional

from mcp_client import ModalMCPClient

class IntegrationTest:
    def __init__(self):
        self.server_process: Optional[subprocess.Popen] = None
        self.client: Optional[ModalMCPClient] = None
    
    def start_server(self):
        print("Starting MCP server...")
        self.server_process = subprocess.Popen(
            ["python", "mcp_server.py"],
            preexec_fn=os.setsid
        )
        
        # Wait for server to start
        time.sleep(2)
        
        try:
            self.client = ModalMCPClient(server_url="http://localhost:8000")
            print("Server is running!")
        except Exception as e:
            if self.server_process:
                os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
                self.server_process.wait()
            raise Exception("Server failed to start")
    
    def stop_server(self):
        if self.server_process:
            print("Stopping MCP server...")
            os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
            self.server_process.wait()
    
    def run_tests(self):
        """Run integration tests."""
        try:
            self.start_server()
            
            # Test deploying an app
            print("\nTesting app deployment...")
            result = self.client.deploy_app("sample_app.py")
            print(f"Deploy result: {result}")
            
            # Test running a function
            print("\nTesting function run...")
            result = self.client.run_function(
                "sample_app.py",
                "hello",
                name="Integration test"
            )
            print(f"Run result: {result}")
            
        finally:
            self.stop_server()

if __name__ == "__main__":
    test = IntegrationTest()
    test.run_tests() 