from contextlib import asynccontextmanager
from fastapi import FastAPI, Request  # type: ignore[import]
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse  # type: ignore[import]

from app.database import Base, engine  # type: ignore[import]
from app.routes.transaction import router as transactions_router  # type: ignore[import]
from app.routes.chart import router as chat_router
from app.routes.analytics import router as analytics_router  # type: ignore[import]
from app.routes.budget import router as budget_router
from app.models import budget 
from app.routes.income import router as income_router
from app.models import income  
from app.routes.sms import router as sms_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables ready")
    yield
    # Shutdown: cleanup if needed
    print("[STOP] Shutting down")


app = FastAPI(
    title="AI Finance Analyzer API",
    description="Personal finance tracker with ML category prediction, anomaly detection, and RAG chat",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


# Routers
app.include_router(transactions_router)
app.include_router(chat_router)
app.include_router(analytics_router)
app.include_router(budget_router)
app.include_router(income_router)
app.include_router(sms_router)

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "running",
        "app": "AI Finance Analyzer",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    import os
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload=False)
