"""
Deployment helper — Creates a public URL using ngrok tunnel.
Run this instead of main.py to get a public URL.
"""

import uvicorn
from pyngrok import ngrok
import asyncio
import database
from agents.orchestrator import OrchestratorAgent

# Initialize the orchestrator globally for the lifespan
orchestrator = None


def start_tunnel():
    """Start ngrok tunnel and return public URL."""
    # Connect ngrok tunnel on port 8080
    public_url = ngrok.connect(8080, bind_tls=True)
    print("\n" + "=" * 60)
    print("🌍 PUBLIC URL (share this!):")
    print(f"   {public_url}")
    print(f"   Dashboard: {public_url}/dashboard")
    print("=" * 60 + "\n")
    return public_url


if __name__ == "__main__":
    # Start the ngrok tunnel
    print("🔗 Creating public tunnel...")
    url = start_tunnel()

    # Start the server
    print("🚀 Starting AgentFlow server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
