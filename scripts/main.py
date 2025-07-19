"""Main FastAPI application for the AI Travel Assistant."""
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from contextlib import asynccontextmanager
from loguru import logger
import sys

from config import settings
from api_routes import router  # Your router with TripXplo routes included
from database import db_manager

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL
)
logger.add(
    settings.LOG_FILE,
    rotation="1 day",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=settings.LOG_LEVEL
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting AI Travel Assistant API")
    
    # Initialize database
    try:
        # Create tables if they don't exist
        from database import Base, engine
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    # Verify DeepSeek API configuration
    if not settings.DEEPSEEK_API_KEY:
        logger.warning("DEEPSEEK_API_KEY not set - using mock responses")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Travel Assistant API")

# Create FastAPI application
app = FastAPI(
    title="AI Travel Assistant API",
    description="A robust AI-powered travel assistant backend system using FastAPI, LangGraph, and DeepSeek LLM",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": getattr(request.state, "request_id", None)
        }
    )

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    import time
    import uuid
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    # Log request
    logger.info(
        f"Request {request_id}: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Response {request_id}: {response.status_code} "
        f"({process_time:.3f}s)"
    )
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    return response

# Include API routes (includes TripXplo endpoints)
app.include_router(router, prefix="/api/v1", tags=["Travel Assistant"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "AI Travel Assistant API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health",
        "features": [
            "Multi-turn conversations with DeepSeek LLM",
            "Flight and hotel search",
            "Booking management",
            "Conversation persistence",
            "LangGraph workflow orchestration",
            "TripXplo package management"
        ]
    }

# New: Simple chat UI page with input box and button
@app.get("/chat-ui", response_class=HTMLResponse)
async def chat_ui():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Travel Assistant Chat</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            #chat-box { border: 1px solid #ccc; padding: 10px; height: 300px; overflow-y: auto; }
            #user-input { width: 80%; padding: 10px; font-size: 16px; }
            #send-btn { padding: 10px; font-size: 16px; }
            .user-msg { color: blue; margin: 5px 0; }
            .bot-msg { color: green; margin: 5px 0; }
        </style>
    </head>
    <body>
        <h2>AI Travel Assistant Chat</h2>
        <div id="chat-box"></div>
        <input type="text" id="user-input" placeholder="Enter your query here..." />
        <button id="send-btn">Send</button>

        <script>
            const chatBox = document.getElementById("chat-box");
            const userInput = document.getElementById("user-input");
            const sendBtn = document.getElementById("send-btn");

            function appendMessage(text, className) {
                const p = document.createElement("p");
                p.textContent = text;
                p.className = className;
                chatBox.appendChild(p);
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            sendBtn.onclick = async () => {
                const message = userInput.value.trim();
                if (!message) return;

                appendMessage("You: " + message, "user-msg");
                userInput.value = "";
                
                try {
                    const response = await fetch("/api/v1/chat", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            message: message,
                            session_id: "default-session",
                            user_id: null
                        })
                    });
                    const data = await response.json();
                    appendMessage("AI: " + data.message, "bot-msg");
                } catch (error) {
                    appendMessage("Error contacting server.", "bot-msg");
                }
            };

            userInput.addEventListener("keypress", function(event) {
                if (event.key === "Enter") {
                    sendBtn.click();
                    event.preventDefault();
                }
            });
        </script>
    </body>
    </html>
    """
    return html_content

# Run the application
if __name__ == "__main__":
    logger.info(f"Starting server on {settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
