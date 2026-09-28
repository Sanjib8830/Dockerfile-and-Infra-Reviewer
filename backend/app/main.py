"""FastAPI application entrypoint: router registration and exception-handler wiring."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.routes.review import router as review_router
from app.core.errors import ReviewApiError

app = FastAPI(title="Dockerfile & Infra Reviewer API")
app.include_router(review_router)


@app.exception_handler(ReviewApiError)
async def handle_review_api_error(_request, exc: ReviewApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.detail)
