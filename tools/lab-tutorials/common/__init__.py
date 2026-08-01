"""Shared paths and env for lab tutorial recording."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TUTORIALS = Path(__file__).resolve().parents[1]
OUT = TUTORIALS / "out"
MEDIA = ROOT / "learn" / "media"

IIQ_BASE = os.environ.get("IIQ_BASE_URL", "http://localhost:8080/identityiq").rstrip("/")
IIQ_USER = os.environ.get("IIQ_USER", "spadmin")
IIQ_PASSWORD = os.environ.get("IIQ_PASSWORD", "admin")
IIQ_DOCKER_CONTAINER = os.environ.get("IIQ_DOCKER_CONTAINER", "mnb-identityiq")

# Path IIQ (inside container) uses for Delimited File
HR_FILE_DOCKER = "/opt/iiq-lab-data/HRApplications.txt"

VIEWPORT = {"width": 1280, "height": 720}
