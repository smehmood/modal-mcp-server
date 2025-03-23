"""Example Modal application."""
import modal

app = modal.App("example-app")

@app.function()
def hello():
    """Simple function that returns a greeting."""
    return "Hello from Modal!" 