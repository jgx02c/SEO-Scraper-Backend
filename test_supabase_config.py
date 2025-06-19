#!/usr/bin/env python3
import os
import sys
sys.path.append('/Users/joshuagoodman/Documents/GitHub/SEO-Scraper-Backend')

from dotenv import load_dotenv
load_dotenv()

print('=== Supabase Configuration Check ===')
print(f'SUPABASE_URL: {os.getenv("SUPABASE_URL")}')
print(f'SUPABASE_KEY length: {len(os.getenv("SUPABASE_KEY", ""))}')
print(f'SUPABASE_SERVICE_KEY length: {len(os.getenv("SUPABASE_SERVICE_KEY", ""))}')
print(f'Keys are different: {os.getenv("SUPABASE_KEY") != os.getenv("SUPABASE_SERVICE_KEY")}')

print('\n=== Testing Admin Client ===')
try:
    from app.db.supabase import admin_supabase
    print('✅ Admin client imported successfully')
    
    # Test a simple read operation
    try:
        response = admin_supabase.table('user_profiles').select('*').limit(1).execute()
        print(f'✅ Admin client can read user_profiles table: {len(response.data) if response.data else 0} rows')
    except Exception as e:
        print(f'❌ Admin client read test failed: {e}')
    
    # Test RLS bypass - try to insert a test record (and delete it)
    test_user_id = '00000000-0000-0000-0000-000000000000'
    try:
        # Try to insert
        insert_response = admin_supabase.table('user_profiles').insert({
            'auth_user_id': test_user_id,
            'email': 'test@example.com',
            'name': 'Test User',
            'plan_type': 'free',
            'subscription_status': 'active'
        }).execute()
        print('✅ Admin client can insert into user_profiles (RLS bypassed)')
        
        # Clean up - delete the test record
        delete_response = admin_supabase.table('user_profiles').delete().eq('auth_user_id', test_user_id).execute()
        print('✅ Test record cleaned up')
        
    except Exception as e:
        print(f'❌ Admin client insert test failed: {e}')
        print('This suggests RLS is still blocking the service role')

except Exception as e:
    print(f'❌ Failed to import admin client: {e}') 