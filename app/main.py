from fastapi import FastAPI

app = FastAPI()


# Test route
@app.get("/")
def welcome_screen():
    return "Hello World!"
