import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from utils.appointment import _has_overlapping_staff_appointments
from utils.blocked_time import (
    _get_blocked_times_by_outlet_and_date,
    _has_overlapping_blocked_times,
)
from utils.shift import _is_within_staff_shift
from utils.time_off import _has_overlapping_time_offs

from app.models.staff.blocked_time import BlockedTimeResponse, BlockedTimeUpsert
from db.supabase import supabase

logger = logging.getLogger(__name__)

blocked_time_router = APIRouter(
    prefix="/api/blocked-times",
    tags=["blocked-times"],
)


@blocked_time_router.get(
    "/outlet/{outlet_id}/{date}", response_model=List[BlockedTimeResponse]
)
def get_blocked_times_for_outlet_and_date(outlet_id: int, date: str):
    if outlet_id not in [1, 2]:
        raise HTTPException(status_code=400, detail="Invalid outlet id")

    try:
        result = _get_blocked_times_by_outlet_and_date(outlet_id, date)
        return result

    except Exception as e:
        logger.error(
            f"Error fetching blocked times for outlet {outlet_id} over date {date}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to get outlet blocked times"
        )


@blocked_time_router.get("/{blocked_time_id}", response_model=BlockedTimeResponse)
def get_single_blocked_time(blocked_time_id: int):
    try:
        blocked_time = (
            supabase.from_("blocked_times")
            .select("*")
            .eq("id", blocked_time_id)
            .limit(1)
            .execute()
        )

        if not blocked_time.data:
            raise HTTPException(status_code=404, detail="Blocked time not found")

        return blocked_time.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching blocked time {blocked_time_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to get blocked time")


# Create
@blocked_time_router.put("", status_code=201)
def create_blocked_time(blocked_time_data: BlockedTimeUpsert):
    return _upsert_blocked_time(None, blocked_time_data)


# Update
@blocked_time_router.put("/{blocked_time_id}")
def update_blocked_time(blocked_time_id: int, blocked_time_data: BlockedTimeUpsert):
    return _upsert_blocked_time(blocked_time_id, blocked_time_data)


# Helper to handle both
def _upsert_blocked_time(
    blocked_time_id: Optional[int], blocked_time_data: BlockedTimeUpsert
):
    # Construct payload
    payload = blocked_time_data.model_dump(exclude_unset=True, by_alias=False)

    if blocked_time_id is not None:
        payload["id"] = blocked_time_id

    # Extract important info
    staff_id = blocked_time_data.staff_id

    staff_response = (
        supabase.from_("staffs").select("*").eq("id", staff_id).single().execute()
    )

    staff = staff_response.data
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    date_string = blocked_time_data.start_date.isoformat()  # YYYY-MM-DD

    blocked_time_start = datetime.combine(
        blocked_time_data.start_date, blocked_time_data.from_time
    )
    is_weekday = blocked_time_start.weekday() >= 0 and blocked_time_start.weekday() <= 4

    blocked_time_start_time = blocked_time_data.from_time.strftime("%H:%M")
    blocked_time_end_time = blocked_time_data.to_time.strftime("%H:%M")

    """ 
        [Cross check error handling]
        1) If cross check fails, it raises a HTTPException
        2) Hence, we just propogate the HTTPException back up 
    """

    try:
        # [CROSS CHECK 1]: Blocked time falls within staff shift hours
        _is_within_staff_shift(
            staff_id,
            staff,
            date_string,
            blocked_time_start_time,
            blocked_time_end_time,
            is_weekday,
            "Blocked time",
        )

        # [CROSS CHECK 2]: Blocked time does not clash with staff appointments
        _has_overlapping_staff_appointments(
            staff_id,
            staff,
            date_string,
            blocked_time_start_time,
            blocked_time_end_time,
            "Blocked time",
        )

        # [CROSS CHECK 3]: Blocked time does not clash with other blocked times
        _has_overlapping_blocked_times(
            staff_id,
            staff,
            date_string,
            blocked_time_start_time,
            blocked_time_end_time,
            "Blocked time",
            blocked_time_id=blocked_time_id,  # Exclude itself
        )

        # [CROSS CHECK 4]: Blocked time does not clash with time offs
        _has_overlapping_time_offs(
            staff_id,
            staff,
            date_string,
            blocked_time_start_time,
            blocked_time_end_time,
            "Blocked time",
        )

        # After passing the cross checks
        # Then only do we perform the upsert
        response = supabase.from_("blocked_times").upsert(payload).execute()

        if blocked_time_id and not response.data:
            raise HTTPException(
                status_code=404, detail="Blocked time to be updated not found"
            )

        return (
            "Blocked time successfully updated"
            if blocked_time_id
            else "Blocked time successfully created"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upserting blocked time: {str(e)}", exc_info=True)

        action = "update" if blocked_time_id else "create"
        raise HTTPException(
            status_code=500, detail=f"Failed to {action} single blocked time"
        )


@blocked_time_router.delete("/{blocked_time_id}")
def delete_blocked_time(blocked_time_id: int):
    try:
        response = (
            supabase.from_("blocked_times").delete().eq("id", blocked_time_id).execute()
        )

        if not response.data:
            raise HTTPException(status_code=404, detail="Blocked time not found")

        return "Blocked time successfully deleted"

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error deleting blocked time {blocked_time_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Failed to delete single blocked time"
        )
