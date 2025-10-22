"""
Test server startup independently
"""
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    logger.info("Step 1: Importing FastAPI...")
    from fastapi import FastAPI
    logger.info("✅ FastAPI imported")
    
    logger.info("Step 2: Importing routes...")
    from api.routes import router, initialize_models
    logger.info("✅ Routes imported")
    
    logger.info("Step 3: Creating app...")
    app = FastAPI()
    logger.info("✅ App created")
    
    logger.info("Step 4: Including router...")
    app.include_router(router)
    logger.info("✅ Router included")
    
    logger.info("Step 5: Initializing models...")
    initialize_models()
    logger.info("✅ Models initialized")
    
    logger.info("\n🎉 ALL STEPS SUCCESSFUL - Server ready to start!")
    logger.info("You can now run: uvicorn main:app --host 0.0.0.0 --port 8000")
    
except KeyboardInterrupt:
    logger.error("❌ KeyboardInterrupt detected!")
    sys.exit(1)
except Exception as e:
    logger.error(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
