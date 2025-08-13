import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from utils.time_off import _get_time_offs_by_outlet_and_date

from app.models.staff.time_off import TimeOffResponse, TimeOffUpsert
from db.supabase import supabase

logger = logging.getLogger(__name__)

time_off_router = APIRouter(
    prefix="/api/time-offs",
    tags=["time-offs"],
)


@time_off_router.get("/outlet/{outlet_id}/{date}", response_model=List[TimeOffResponse])
def get_time_offs_for_outlet_and_date(outlet_id: int, date: str):
    if outlet_id not in [1, 2]:
        raise HTTPException(status_code=400, detail="Invalid outlet id")

    try:
        result = _get_time_offs_by_outlet_and_date(outlet_id, date)
        return result

    except Exception as e:
        logger.error(
            f"Error fetching time offs for outlet {outlet_id} over date {date}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to get outlet time offs")


@time_off_router.get("/{time_off_id}", response_model=TimeOffResponse)
def get_single_time_off(time_off_id: int):
    try:
        time_off = (
            supabase.from_("time_offs")
            .select("*")
            .eq("id", time_off_id)
            .limit(1)
            .execute()
        )

        if not time_off.data:
            raise HTTPException(status_code=404, detail="Time off not found")

        return time_off.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching time off {time_off_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get time off")


# Create
@time_off_router.put("", status_code=201)
def create_time_off(time_off_data: TimeOffUpsert):
    return _upsert_time_off(None, time_off_data)


# Update
@time_off_router.put("/{time_off_id}")
def update_time_off(time_off_id: int, time_off_data: TimeOffUpsert):
    return _upsert_time_off(time_off_id, time_off_data)


# Helper to handle both
def _upsert_time_off(time_off_id: Optional[int], time_off_data: TimeOffUpsert):
    # Construct payload
    payload = time_off_data.model_dump(exclude_unset=True, by_alias=False)

    if time_off_data is not None:
        payload["id"] = time_off_data

    # [CROSS CHECK 1]: Time off falls within staff shift hours

    # [CROSS CHECK 2]: Time off does not clash with staff appointments

    # [CROSS CHECK 3]: Time off does not clash with blocked times

    # [CROSS CHECK 4]: Time off does not clash with other time offs

    # After passing the cross checks
    # Then only do we perform the upsert
        
