import uvicorn
from api import app
import sys

if __name__ == "__main__":
    port = 8002
    if len(sys.argv) > 1 and sys.argv[1] == "--port":
        port = int(sys.argv[2])
    
    print(f"Starting FastAPI Server on port {port}...")
    try:
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        print(f"Server failed to start: {e}")
