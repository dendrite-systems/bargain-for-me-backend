from supabase import create_client, Client
from dotenv import load_dotenv
import os


supabase_url = 'https://rwxfugtllmxiztocfuhf.supabase.co'
supabase_key = os.getenv("supa_pwd")
print(supabase_key)
supabase: Client = create_client(supabase_url, supabase_key)
# bucket_name=""

# res = supabase.storage.from_(bucket_name).list()

# with open(filepath, 'rb') as f:
	
# 	supabase.storage.from_(bucket_name).upload(file=f,path=path_on_supastorage)
