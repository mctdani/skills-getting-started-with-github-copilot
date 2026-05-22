"""Pytest configuration and fixtures for FastAPI tests"""

import pytest
from copy import deepcopy
from fastapi.testclient import TestClient
from src.app import app, activities as original_activities


@pytest.fixture
def app_state():
    """
    Fixture to reset in-memory database state before each test.
    Provides a deep copy of the original activities data.
    """
    # Store a backup of the original activities state
    backup = deepcopy(original_activities)
    yield
    # Restore the original state after the test
    original_activities.clear()
    original_activities.update(deepcopy(backup))


@pytest.fixture
def client(app_state):
    """
    Fixture providing a TestClient for the FastAPI app.
    Uses the app_state fixture to ensure fresh database state per test.
    """
    return TestClient(app)
