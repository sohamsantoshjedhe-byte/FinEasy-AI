"""
FinEasy AI - Mock Government API Application
Simulates the Income Tax Department (ITD) e-Filing & CPC endpoints for educational demos.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mock_government.routes import auth, prefill, validation, submission

app = FastAPI(
    title="Mock Government Tax Portal API (DEMO)",
    description="Educational simulation of the Indian Income Tax Department e-Filing API endpoints. NOT CONNECTED TO REAL GOVERNMENT SYSTEMS.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(prefill.router)
app.include_router(validation.router)
app.include_router(submission.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": "Mock Government Tax Portal API",
        "status": "online",
        "mode": "EDUCATIONAL_DEMO",
        "notice": "THIS SERVICE IS A SIMULATION AND DOES NOT INTERACT WITH REAL GOVERNMENT SYSTEMS",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mock_government.main:app", host="127.0.0.1", port=8001, reload=True)
