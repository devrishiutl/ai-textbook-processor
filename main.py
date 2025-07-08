"""
Simple Main Entry Point
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("routes.route:app", host="0.0.0.0", port=8003, reload=True) 