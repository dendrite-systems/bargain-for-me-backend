from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()
supabase_url = 'https://rwxfugtllmxiztocfuhf.supabase.co'
supabase_key = os.getenv("supa_pwd")
print(supabase_key)
supabase: Client = create_client(supabase_url, supabase_key)
# bucket_name=""

# res = supabase.storage.from_(bucket_name).list()

# with open(filepath, 'rb') as f:
	
# 	supabase.storage.from_(bucket_name).upload(file=f,path=path_on_supastorage)


def sign_up(email: str, password: str):
    """Sign up a new user."""
    response = supabase.auth.sign_up({
        'email': email,
        'password': password
    })
    return response

def sign_in_with_password(email: str, password: str):
    """Sign in an existing user with email and password."""
    response = supabase.auth.sign_in_with_password({
        'email': email,
        'password': password
    })
    return response

def get_user():
    """Get the currently authenticated user."""
    user = supabase.auth.get_user()
    return user

def sign_out():
    """Sign out the currently authenticated user."""
    response = supabase.auth.sign_out()
    return response



if __name__ == "__main__":
    # Example usage
    email = "user2@example.com"
    password = "password123"

    # Sign up a new user
    sign_up_response = sign_up(email, password)
    print("Sign Up Response:", sign_up_response)

    # Sign in an existing user
    sign_in_response = sign_in_with_password(email, password)
    print("Sign In Response:", sign_in_response)

    # Get the currently authenticated user
    user = get_user()
    print("Authenticated User:", user)

    # Sign out the currently authenticated user
    sign_out_response = sign_out()
    print("Sign Out Response:", sign_out_response)
