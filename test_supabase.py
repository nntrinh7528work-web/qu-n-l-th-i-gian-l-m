# Simulate Streamlit secrets test
import os
import sys

# Set env vars first
os.environ["SUPABASE_URL"] = "https://yujokjmqbqqdvpentrtt.supabase.co"
os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl1am9ram1xYnFxZHZwZW50cnR0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDExNDgyMCwiZXhwIjoyMDg1NjkwODIwfQ.-7FQcbbWZA3w7I6S8-AWSuBGHcK465OUlt5ataj496I"

print("=" * 50)
print("TEST 1: Import supabase_db module")
print("=" * 50)

try:
    import supabase_db
    print("SUCCESS: supabase_db imported")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("TEST 2: Check is_supabase_available()")
print("=" * 50)

try:
    result = supabase_db.is_supabase_available()
    print(f"is_supabase_available() = {result}")
    if result:
        print("SUCCESS: Supabase is available!")
    else:
        print("WARNING: Supabase not available - checking why...")
        
        # Debug: Check client
        client = supabase_db.get_supabase_client()
        print(f"get_supabase_client() = {client}")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("TEST 3: Check auth module")  
print("=" * 50)

try:
    import user_auth as auth
    result = auth._check_supabase()
    print(f"auth._check_supabase() = {result}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("TEST 4: Check db_wrapper module")
print("=" * 50)

try:
    import db_wrapper as db
    result = db._check_supabase()
    print(f"db._check_supabase() = {result}")
    print(f"db.is_cloud_mode() = {db.is_cloud_mode()}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("DONE")
print("=" * 50)
