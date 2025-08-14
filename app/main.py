from fastapi import FastAPI

from app.routes.appointment.appointment import appointment_router
from app.routes.customer import customer_router
from app.routes.outlet import outlet_router
from app.routes.service.category import category_router
from app.routes.service.category_color import category_color_router
from app.routes.service.service import service_router
from app.routes.staff.blocked_time import blocked_time_router
from app.routes.staff.shift import shift_router
from app.routes.staff.staff import staff_router
from app.routes.staff.time_off import time_off_router

app = FastAPI()


""" Router registration """

# Routers managing services
app.include_router(category_color_router)
app.include_router(category_router)
app.include_router(service_router)

# Routers managing staffs
app.include_router(staff_router)
app.include_router(shift_router)
app.include_router(time_off_router)
app.include_router(blocked_time_router)

# Router managing others
app.include_router(appointment_router)
app.include_router(customer_router)
app.include_router(outlet_router)


# Test route
@app.get("/")
def welcome_screen():
    return "Hello World!"
