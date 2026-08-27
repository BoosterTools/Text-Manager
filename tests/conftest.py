from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.db import Database
from app.services.expression_service import ExpressionService
from app.services.session_service import SessionService
from app.services.settings_service import SettingsService


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / "test.db")
    yield database
    database.close()


@pytest.fixture
def expression_service(db):
    return ExpressionService(db)


@pytest.fixture
def session_service(db):
    return SessionService(db)


@pytest.fixture
def settings_service(db):
    return SettingsService(db)
