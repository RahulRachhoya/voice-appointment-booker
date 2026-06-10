"""Booking manager: slot management and appointment creation."""

import logging
from dataclasses import dataclass, field
from datetime import date

log = logging.getLogger(__name__)


@dataclass
class Appointment:
    """Lightweight appointment record (in-memory or persisted via SQLModel)."""

    id: int
    customer_name: str
    appointment_date: str  # ISO date: "2025-01-15"
    appointment_time: str  # "10:00"
    service_type: str = "Standard appointment"
    customer_phone: str = ""
    status: str = "confirmed"


@dataclass
class BookingManager:
    """Manages available slots and appointment bookings.

    Slots are stored as a dict keyed by "YYYY-MM-DD HH:MM".
    Value is None when available, or an Appointment when booked.
    """

    _slots: dict[str, Appointment | None] = field(default_factory=dict)
    _next_id: int = field(default=1)

    def __post_init__(self) -> None:
        """Seed default available slots for the next 7 weekdays."""
        self._seed_default_slots()

    def _seed_default_slots(self) -> None:
        """Populate a set of default time slots."""
        from datetime import timedelta

        today = date.today()
        slot_times = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
        added = 0
        delta = 0
        while added < 7:
            day = today + timedelta(days=delta)
            delta += 1
            if day.weekday() >= 5:  # skip weekends
                continue
            for t in slot_times:
                key = f"{day.isoformat()} {t}"
                self._slots[key] = None
            added += 1

    def list_available(self) -> list[str]:
        """Return list of available slot keys (not yet booked)."""
        return sorted(k for k, v in self._slots.items() if v is None)

    def book_slot(
        self,
        appointment_date: str,
        appointment_time: str,
        customer_name: str,
        service_type: str = "Standard appointment",
        customer_phone: str = "",
    ) -> Appointment:
        """Book a slot and return the created Appointment.

        Args:
            appointment_date: ISO date string e.g. "2025-01-15".
            appointment_time: Time string e.g. "10:00".
            customer_name: Name of the customer.
            service_type: Type of appointment.
            customer_phone: Optional phone number.

        Returns:
            Created Appointment dataclass.

        Raises:
            ValueError: If the slot is not available.
        """
        key = f"{appointment_date} {appointment_time}"
        if key not in self._slots:
            # Add slot dynamically if not pre-seeded
            self._slots[key] = None

        if self._slots[key] is not None:
            raise ValueError(f"Slot {key} is already booked")

        appointment = Appointment(
            id=self._next_id,
            customer_name=customer_name,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            service_type=service_type,
            customer_phone=customer_phone,
        )
        self._slots[key] = appointment
        self._next_id += 1
        log.info("Booked slot %s for %s", key, customer_name)
        return appointment

    def cancel_slot(self, appointment_id: int) -> bool:
        """Cancel an appointment by ID. Returns True if found and cancelled."""
        for key, appt in self._slots.items():
            if appt is not None and appt.id == appointment_id:
                self._slots[key] = None
                log.info("Cancelled appointment %d", appointment_id)
                return True
        return False

    def get_all_appointments(self) -> list[Appointment]:
        """Return all booked appointments."""
        return [a for a in self._slots.values() if a is not None]


# Module-level singleton
_manager: BookingManager | None = None


def get_booking_manager() -> BookingManager:
    """Return the shared BookingManager instance."""
    global _manager
    if _manager is None:
        _manager = BookingManager()
    return _manager
