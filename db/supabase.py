import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")


# Our client object that links to the supabase db
supabase: Client = create_client(url, key)
