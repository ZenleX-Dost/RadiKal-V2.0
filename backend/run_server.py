"""
Simple server startup without reload to avoid Windows multiprocessing issues
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload to avoid multiprocessing issues on Windows
        log_level="info"
    )
