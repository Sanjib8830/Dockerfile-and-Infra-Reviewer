"""FastAPI application entrypoint: router registration and exception-handler wiring."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.review import router as review_router
from app.core.errors import ReviewApiError

app = FastAPI(title="Dockerfile & Infra Reviewer API")
allowed_origins = [
    origin.strip()
    for origin in os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)
app.include_router(review_router)


@app.exception_handler(ReviewApiError)
async def handle_review_api_error(_request, exc: ReviewApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.detail)
