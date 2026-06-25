import uvicorn
from app.config import settings

if __name__ == "__main__":
    # This entrypoint allows setting breakpoints in IDEs by running debug.py directly
    print("Starting FastAPI app in debug mode...")
    uvicorn.run(
        "main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.RELOAD, 
        log_level="debug"
    )
