"""
Server startup script without reload for Windows compatibility
"""
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting RadiKal backend server...")
    logger.info("Server will run on http://0.0.0.0:8000")
    logger.info("Press CTRL+C to stop")
    
    # Run without reload to avoid Windows multiprocessing issues
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload for Windows
        log_level="info",
        access_log=True,
    )
