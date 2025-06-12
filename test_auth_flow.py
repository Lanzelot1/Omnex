#!/usr/bin/env python3
"""Test the complete authentication flow."""

import asyncio
import httpx
import json
from uuid import uuid4

BASE_URL = "http://localhost:8000"

async def test_auth_flow():
    """Test the complete authentication flow."""
    async with httpx.AsyncClient() as client:
        print("🚀 Testing Omnex Authentication Flow\n")
        
        # 1. Register a new user
        print("1️⃣ Registering new user...")
        register_data = {
            "email": f"test_{uuid4().hex[:8]}@example.com",
            "password": "SecurePassword123!",
            "name": "Test User"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
            if response.status_code == 201:
                user_data = response.json()
                print(f"✅ User registered: {user_data['email']}")
                access_token = user_data['access_token']
                refresh_token = user_data['refresh_token']
            else:
                print(f"❌ Registration failed: {response.text}")
                return
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Make sure the server is running with: make docker-up && make run")
            return
        
        # 2. Get current user info
        print("\n2️⃣ Getting current user info...")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
        if response.status_code == 200:
            me_data = response.json()
            print(f"✅ Current user: {me_data['email']} (ID: {me_data['id']})")
        else:
            print(f"❌ Failed to get user info: {response.text}")
        
        # 3. Create an API key
        print("\n3️⃣ Creating API key...")
        api_key_data = {
            "name": "Test API Key",
            "scopes": ["read", "write"]
        }
        response = await client.post(f"{BASE_URL}/api/v1/auth/api-keys", 
                                   json=api_key_data, headers=headers)
        if response.status_code == 201:
            api_key_response = response.json()
            api_key = api_key_response['key']
            api_key_id = api_key_response['id']
            print(f"✅ API key created: {api_key_response['prefix']}...")
            print(f"   Full key (save this!): {api_key}")
        else:
            print(f"❌ Failed to create API key: {response.text}")
        
        # 4. Test JWT auth with context creation
        print("\n4️⃣ Testing JWT auth - Creating context...")
        context_data = {
            "namespace": "test-namespace",
            "key": "test-key",
            "value": {"message": "Hello from JWT auth!"},
            "tags": ["test", "jwt"]
        }
        response = await client.post(f"{BASE_URL}/api/v1/context/", 
                                   json=context_data, headers=headers)
        if response.status_code == 201:
            context = response.json()
            print(f"✅ Context created with JWT auth: {context['namespace']}/{context['key']}")
        else:
            print(f"❌ Failed to create context: {response.text}")
        
        # 5. Test API key auth
        print("\n5️⃣ Testing API key auth - Getting context...")
        api_headers = {"Authorization": f"Bearer {api_key}"}
        response = await client.get(
            f"{BASE_URL}/api/v1/context/{context_data['namespace']}/{context_data['key']}", 
            headers=api_headers
        )
        if response.status_code == 200:
            retrieved = response.json()
            print(f"✅ Context retrieved with API key: {retrieved['value']}")
        else:
            print(f"❌ Failed to get context with API key: {response.text}")
        
        # 6. Test memory storage
        print("\n6️⃣ Testing memory storage...")
        memory_data = {
            "content": "This is a test memory created during auth testing.",
            "metadata": {"source": "auth_test", "timestamp": "2024-12-06"}
        }
        response = await client.post(f"{BASE_URL}/api/v1/memory/", 
                                   json=memory_data, headers=headers)
        if response.status_code == 201:
            memory = response.json()
            print(f"✅ Memory created: {memory['id']}")
        else:
            print(f"❌ Failed to create memory: {response.text}")
        
        # 7. Test memory search
        print("\n7️⃣ Testing memory search...")
        search_data = {
            "query": "auth testing",
            "limit": 10
        }
        response = await client.post(f"{BASE_URL}/api/v1/memory/search", 
                                   json=search_data, headers=headers)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Memory search returned {len(results)} results")
        else:
            print(f"❌ Failed to search memories: {response.text}")
        
        # 8. Test token refresh
        print("\n8️⃣ Testing token refresh...")
        refresh_data = {"refresh_token": refresh_token}
        response = await client.post(f"{BASE_URL}/api/v1/auth/refresh", json=refresh_data)
        if response.status_code == 200:
            refresh_response = response.json()
            new_access_token = refresh_response['access_token']
            print("✅ Token refreshed successfully")
        else:
            print(f"❌ Failed to refresh token: {response.text}")
        
        # 9. Test logout
        print("\n9️⃣ Testing logout...")
        response = await client.post(f"{BASE_URL}/api/v1/auth/logout", headers=headers)
        if response.status_code == 200:
            print("✅ Logged out successfully")
        else:
            print(f"❌ Failed to logout: {response.text}")
        
        print("\n✨ Authentication flow test completed!")


if __name__ == "__main__":
    print("""
    ========================================
    Omnex Authentication Flow Test
    ========================================
    
    Prerequisites:
    1. Start Docker services: make docker-up
    2. Run database migrations: make db-migrate
    3. Start the API server: make run
    
    Then run this script to test the auth flow.
    ========================================
    """)
    
    asyncio.run(test_auth_flow())