from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

# Import all routers
from .routers import (
    companies,
    screener,
    sectors,
    peers,
    valuation,
    portfolio,
    documents,
    health,
)

app = FastAPI(
    title="Nifty 100 API",
    description="REST API for Nifty 100 Financial Analytics Platform",
    version="1.0.0",
)

# CORS Middleware (Internal use only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"[{request.method}] {request.url.path} - {process_time:.4f}s")
    return response


# Register Routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1/companies", tags=["Companies"])
app.include_router(screener.router, prefix="/api/v1/screener", tags=["Screener"])
app.include_router(sectors.router, prefix="/api/v1/sectors", tags=["Sectors"])
app.include_router(peers.router, prefix="/api/v1/peers", tags=["Peers"])
app.include_router(valuation.router, prefix="/api/v1/valuation", tags=["Valuation"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["Portfolio"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
