"""
Custom server startup script with error handling
"""
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    logger.info("Starting server...")
    import uvicorn
    
    # Run without reload to avoid issues
    # Suppress the default signal handlers to prevent auto-shutdown
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
        reload=False,
        # Remove signal handlers to prevent interruption
        use_colors=True,
    )
    
except KeyboardInterrupt:
    logger.info("Server stopped by user")
except Exception as e:
    logger.error(f"Server error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
