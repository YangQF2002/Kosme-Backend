from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

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


""" Guard against web crawlers (recursively follows links) """


# Middleware to augment responses
@app.middleware("http")
async def add_robot_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


# Robots.txt file to tell search engine to restrict crawlers from URL access
@app.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    data = """User-agent: *\nDisallow: /"""
    return data


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


# Relaxed CORS policy
# For browser clients to communicate with this server
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
