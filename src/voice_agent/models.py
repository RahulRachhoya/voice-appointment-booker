"""SQLModel table definitions for appointments."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class AppointmentBase(SQLModel):
    """Shared appointment fields."""

    customer_name: str
    customer_phone: str = ""
    service_type: str = "Standard appointment"
    appointment_date: str  # ISO date string e.g. "2025-01-15"
    appointment_time: str  # e.g. "10:00"
    notes: str = ""


class Appointment(AppointmentBase, table=True):
    """Database table for appointments."""

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "confirmed"  # confirmed | cancelled | completed


class AppointmentCreate(AppointmentBase):
    """Schema for creating an appointment via API."""


class AppointmentRead(AppointmentBase):
    """Schema for reading an appointment from the API."""

    id: int
    created_at: datetime
    status: str
