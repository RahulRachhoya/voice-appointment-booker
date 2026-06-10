"""Shared pytest fixtures."""

import pytest


@pytest.fixture
def booking_manager():
    """Return a fresh BookingManager for each test."""
    from voice_agent.services.booking import BookingManager

    return BookingManager()
