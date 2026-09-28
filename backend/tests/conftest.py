"""Shared pytest fixtures for backend tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


SAMPLE_DOCKERFILE = """FROM python:3.12

WORKDIR /app

COPY . .

RUN pip install flask requests

EXPOSE 5000

CMD ["python", "app.py"]
"""

SAMPLE_TERRAFORM_PUBLIC_SSH = """resource "aws_security_group" "app" {
  name = "app"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""
