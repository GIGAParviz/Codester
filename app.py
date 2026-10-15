import sqlite3
import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from llm_provider import LLMProviderError, extract_query, provider_config
from scripts.search_mesc import DB_PATH, parse_query, search_parsed


app = FastAPI(title="MESC Copilot API", version="0.1.0")
logger = logging.getLogger("mesc_copilot")
ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=10, ge=1, le=50)
    use_ai: bool = True


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    logger.exception("Unhandled request error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "error_type": type(exc).__name__})


def merge_query(heuristic: dict[str, Any], model_query: dict[str, Any]):
    merged = dict(heuristic)
    for key, value in model_query.items():
        if value not in (None, "", []):
            merged[key] = value
    return merged


@app.get("/health")
def health():
    configured = provider_config()
    return {"status": "ok", "catalog_exists": DB_PATH.exists(), "llm_provider": configured["provider"], "llm_configured": bool(configured["api_key"])}


@app.get("/stats")
def stats():
    if not DB_PATH.exists():
        return {"catalog_exists": False, "rows": 0, "active_rows": 0}
    connection = sqlite3.connect(DB_PATH)
    total = connection.execute("SELECT COUNT(*) FROM catalog").fetchone()[0]
    active = connection.execute("SELECT COUNT(*) FROM catalog WHERE status = 'ACTIVE'").fetchone()[0]
    connection.close()
    return {"catalog_exists": True, "rows": total, "active_rows": active}


@app.post("/search")
def search(request: SearchRequest):
    heuristic = parse_query(request.query)
    parsed = heuristic
    ai_used = False
    ai_error = None
    if request.use_ai:
        try:
            parsed = merge_query(heuristic, extract_query(request.query))
            ai_used = True
        except LLMProviderError as exc:
            ai_error = str(exc)
    result = search_parsed(request.query, parsed, request.limit)
    return {"query": request.query, "ai_used": ai_used, "ai_error": ai_error, "parsed": result["parsed"], "results": result["results"], "result_count": len(result["results"]), "data_status": "synthetic" if result["results"] and all(item["synthetic"] for item in result["results"]) else "catalogue"}
