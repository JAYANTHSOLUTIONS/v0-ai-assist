"""Script to run the AI Travel Assistant server."""
import asyncio
import uvicorn
from loguru import logger

from config import settings
from main import app

async def main():
    """Main function to run the server."""
    logger.info("🚀 Starting AI Travel Assistant Server")
    logger.info(f"📍 Server will run on http://{settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"📚 API Documentation: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    logger.info(f"🔍 Health Check: http://{settings.API_HOST}:{settings.API_PORT}/api/v1/health")
    
    # Configuration summary
    logger.info("⚙️  Configuration Summary:")
    logger.info(f"   - Database: {settings.DATABASE_URL}")
    logger.info(f"   - DeepSeek API: {'✅ Configured' if settings.DEEPSEEK_API_KEY else '❌ Not configured (using mock)'}")
    logger.info(f"   - Log Level: {settings.LOG_LEVEL}")
    logger.info(f"   - Max Conversation History: {settings.MAX_CONVERSATION_HISTORY}")
    
    # Run the server
    config = uvicorn.Config(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
        raise
