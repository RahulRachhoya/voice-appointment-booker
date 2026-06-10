"""Unit tests for BookingManager."""

import pytest

from voice_agent.services.booking import Appointment, BookingManager


@pytest.fixture
def mgr():
    """Return a fresh BookingManager for each test."""
    return BookingManager()


def test_list_available_returns_slots(mgr: BookingManager):
    """list_available() should return a non-empty list of slot strings."""
    slots = mgr.list_available()
    assert isinstance(slots, list)
    assert len(slots) > 0
    # Each slot should match "YYYY-MM-DD HH:MM" pattern
    for slot in slots[:3]:
        parts = slot.split(" ")
        assert len(parts) == 2, f"Unexpected slot format: {slot}"


def test_book_slot_returns_appointment(mgr: BookingManager):
    """book_slot() should return an Appointment with correct fields."""
    available = mgr.list_available()
    assert available, "No slots available to book"
    slot = available[0]
    date_str, time_str = slot.split(" ")

    appt = mgr.book_slot(
        appointment_date=date_str,
        appointment_time=time_str,
        customer_name="Alice Smith",
        service_type="Initial consultation",
    )

    assert isinstance(appt, Appointment)
    assert appt.customer_name == "Alice Smith"
    assert appt.appointment_date == date_str
    assert appt.appointment_time == time_str
    assert appt.status == "confirmed"


def test_booked_slot_no_longer_available(mgr: BookingManager):
    """After booking, the slot should not appear in list_available()."""
    available_before = mgr.list_available()
    slot = available_before[0]
    date_str, time_str = slot.split(" ")

    mgr.book_slot(date_str, time_str, "Bob Jones")

    available_after = mgr.list_available()
    assert slot not in available_after


def test_double_booking_raises_value_error(mgr: BookingManager):
    """Booking the same slot twice should raise ValueError."""
    available = mgr.list_available()
    slot = available[0]
    date_str, time_str = slot.split(" ")

    mgr.book_slot(date_str, time_str, "Charlie Brown")

    with pytest.raises(ValueError, match="already booked"):
        mgr.book_slot(date_str, time_str, "Diana Prince")


def test_cancel_slot_frees_it(mgr: BookingManager):
    """cancel_slot() should free the slot so it is available again."""
    available = mgr.list_available()
    slot = available[0]
    date_str, time_str = slot.split(" ")

    appt = mgr.book_slot(date_str, time_str, "Eve Adams")
    assert slot not in mgr.list_available()

    result = mgr.cancel_slot(appt.id)
    assert result is True
    assert slot in mgr.list_available()


def test_cancel_nonexistent_returns_false(mgr: BookingManager):
    """cancel_slot() with a bad ID should return False, not raise."""
    result = mgr.cancel_slot(999)
    assert result is False


def test_multiple_appointments_tracked(mgr: BookingManager):
    """Multiple bookings should all appear in get_all_appointments()."""
    available = mgr.list_available()
    booked = []
    for slot in available[:3]:
        date_str, time_str = slot.split(" ")
        appt = mgr.book_slot(date_str, time_str, f"Person {slot}")
        booked.append(appt.id)

    all_appts = mgr.get_all_appointments()
    all_ids = {a.id for a in all_appts}
    for aid in booked:
        assert aid in all_ids


def test_auto_add_custom_slot(mgr: BookingManager):
    """Booking a slot not in the pre-seeded list should succeed."""
    appt = mgr.book_slot(
        appointment_date="2030-06-15",
        appointment_time="08:00",
        customer_name="Future Person",
    )
    assert appt.appointment_date == "2030-06-15"
    assert appt.appointment_time == "08:00"
