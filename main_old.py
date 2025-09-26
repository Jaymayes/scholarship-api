import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.analytics import router as analytics_router
from routers.scholarships import router as scholarships_router
from utils.logger import setup_logger

# Initialize logger
logger = setup_logger()

# Create FastAPI app
app = FastAPI(
    title="Scholarship Discovery & Search API",
    description="A comprehensive scholarship discovery system with search, filtering, and eligibility checking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scholarships_router, prefix="/api/v1", tags=["scholarships"])
app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])

@app.get("/")
async def root():
    """Root endpoint providing API information"""
    return {
        "message": "Scholarship Discovery & Search API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running successfully"}

if __name__ == "__main__":
    logger.info("Starting Scholarship Discovery API server")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )
