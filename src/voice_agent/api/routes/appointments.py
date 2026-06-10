"""Appointments CRUD route."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from voice_agent.services.booking import Appointment, get_booking_manager

log = logging.getLogger(__name__)
router = APIRouter(prefix="/appointments", tags=["appointments"])


class BookRequest(BaseModel):
    customer_name: str
    appointment_date: str
    appointment_time: str
    service_type: str = "Standard appointment"
    customer_phone: str = ""


class BookResponse(BaseModel):
    id: int
    customer_name: str
    appointment_date: str
    appointment_time: str
    service_type: str
    status: str


def _to_response(appt: Appointment) -> BookResponse:
    return BookResponse(
        id=appt.id,
        customer_name=appt.customer_name,
        appointment_date=appt.appointment_date,
        appointment_time=appt.appointment_time,
        service_type=appt.service_type,
        status=appt.status,
    )


@router.get("/available")
async def list_available() -> dict[str, list[str]]:
    """Return list of available time slots."""
    mgr = get_booking_manager()
    return {"slots": mgr.list_available()}


@router.post("/book", response_model=BookResponse)
async def book_appointment(req: BookRequest) -> BookResponse:
    """Book an appointment slot."""
    mgr = get_booking_manager()
    try:
        appt = mgr.book_slot(
            appointment_date=req.appointment_date,
            appointment_time=req.appointment_time,
            customer_name=req.customer_name,
            service_type=req.service_type,
            customer_phone=req.customer_phone,
        )
        return _to_response(appt)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/list")
async def list_appointments() -> dict[str, list[BookResponse]]:
    """List all booked appointments."""
    mgr = get_booking_manager()
    return {"appointments": [_to_response(a) for a in mgr.get_all_appointments()]}


@router.delete("/{appointment_id}")
async def cancel_appointment(appointment_id: int) -> dict[str, str]:
    """Cancel an appointment by ID."""
    mgr = get_booking_manager()
    if not mgr.cancel_slot(appointment_id):
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"status": "cancelled"}
