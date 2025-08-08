from fastapi import FastAPI

from db.supabase import supabase

app = FastAPI()


# Retrieve a user
@app.get("/user")
def get_user():
    try:
        users = supabase.table("users").select("*").execute()
        print(users)
        return users
    except Exception as e:
        print(f"Error: {e}")
        return {"message": "User not found"}
