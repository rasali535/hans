import os
import sys
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Force current directory into path for local imports
sys.path.append(os.path.dirname(__file__))

# Global error capture for imports
IMPORT_ERROR = None
try:
    from agents import run_pipeline, AMD_INFERENCE_URL, AMD_MODEL_NAME, AMD_INFERENCE_TOKEN, generate_social_post
except Exception as e:
    IMPORT_ERROR = f"Import Error: {str(e)}\n{traceback.format_exc()}"

app = FastAPI(title="ForgeSight Debug API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def error_logging_middleware(request: Request, call_next):
    if IMPORT_ERROR:
        return JSONResponse({"status": "error", "message": IMPORT_ERROR}, status_code=500)
    try:
        return await call_next(request)
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

@app.get("/api/health")
@app.get("/_/backend/api/health")
async def health():
    return {"status": "online", "debug": True, "cwd": os.getcwd(), "path": sys.path}

@app.get("/api/inspections")
@app.get("/_/backend/api/inspections")
async def list_inspections():
    return {"items": [], "total": 0, "note": "Debug mode"}

# ... other minimal routes to avoid crashes ...
