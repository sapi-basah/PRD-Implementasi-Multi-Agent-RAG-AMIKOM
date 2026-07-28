import time
import uuid
from fastapi import FastAPI, Request
from app.api.health import router as health_router
from app.observability.logging import logger

app = FastAPI(
    title="Multi-Agent RAG AMIKOM Yogyakarta",
    description="Sistem Layanan Akademik Terpadu S1 Informatika Universitas AMIKOM Yogyakarta",
    version="1.0.0"
)

# Middleware for request ID and latency logging
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    response = await call_next(request)
    latency_ms = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Latency-MS"] = f"{latency_ms:.2f}"
    logger.info(f"Method={request.method} Path={request.url.path} RequestID={request_id} Latency={latency_ms:.2f}ms Status={response.status_code}")
    return response


app.include_router(health_router)

@app.get("/")
def read_root():
    return {
        "service": "Multi-Agent RAG AMIKOM",
        "status": "RUNNING",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
