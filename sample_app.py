"""
Sample Modal app for testing the MCP server.
This app demonstrates basic Modal functionality that can be deployed, served, and run.
"""

import modal
import time
from typing import Dict, List, Optional

# Create a Modal app
app = modal.App("sample-app")

# Define a simple image
image = modal.Image.debian_slim().pip_install(["numpy", "pandas", "scikit-learn", "fastapi[standard]"])

# Simple function that can be run
@app.function()
def hello(name: str = "World") -> str:
    """Simple function that returns a greeting."""
    return f"Hello, {name}!"

@app.function(image=image)
def process_data(data: List[float], operation: str = "sum") -> Dict[str, float]:
    """Process a list of numbers with the specified operation."""
    import numpy as np
    
    result = {
        "input_length": len(data),
        "input_sample": data[:5] if len(data) > 5 else data
    }
    
    if operation == "sum":
        result["result"] = float(np.sum(data))
    elif operation == "mean":
        result["result"] = float(np.mean(data))
    elif operation == "max":
        result["result"] = float(np.max(data))
    elif operation == "min":
        result["result"] = float(np.min(data))
    else:
        result["error"] = f"Unknown operation: {operation}"
    
    return result

# Long-running function to demonstrate background execution
@app.function()
def long_running_task(duration_seconds: int = 30) -> Dict[str, str]:
    """Simulates a long-running task that sleeps for the specified duration."""
    start_time = time.time()
    
    # Simulate work by sleeping
    print(f"Starting long-running task for {duration_seconds} seconds...")
    for i in range(duration_seconds):
        time.sleep(1)
        if i % 5 == 0:
            print(f"Progress: {i}/{duration_seconds} seconds elapsed")
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    return {
        "status": "completed",
        "requested_duration": duration_seconds,
        "actual_duration": elapsed,
        "message": f"Task completed after {elapsed:.2f} seconds"
    }

# Web endpoint for serving
@app.function(image=image)
@modal.fastapi_endpoint()
def web_hello(name: str = "World") -> Dict[str, str]:
    """Web endpoint that returns a greeting in JSON format."""
    return {
        "message": f"Hello, {name}!",
        "timestamp": time.time()
    }

# Another web endpoint for calculations
@app.function(image=image)
@modal.fastapi_endpoint(method="POST")
def web_calculate(item: dict) -> Dict[str, float]:
    """Web endpoint that performs a calculation."""
    operation = item.get("operation", "add")
    a = float(item.get("a", 0))
    b = float(item.get("b", 0))
    
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            return {"error": "Cannot divide by zero"}
        result = a / b
    else:
        return {"error": f"Unknown operation: {operation}"}
    
    return {
        "operation": operation,
        "a": a,
        "b": b,
        "result": result
    }

if __name__ == "__main__":
    with app.run():
        print(hello("Modal")) 