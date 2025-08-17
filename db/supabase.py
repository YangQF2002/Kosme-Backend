import os

from dotenv import load_dotenv
from supabase import Client, acreate_client, create_client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")


# Our client object that links to the supabase db
supabase: Client = create_client(url, key)


# New method to prevent disconnects?
async def get_supabase_client():
    supabase: Client = await acreate_client(url, key)
    return supabase
