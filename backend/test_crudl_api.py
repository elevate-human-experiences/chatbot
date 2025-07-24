# MIT-0 License
#
# Copyright (c) 2025 Elevate Human Experiences, LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# MIT License
#
# Copyright (c) 2025 Elevate Human Experiences, LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Test script to verify all CRUDL routes are working properly."""

import asyncio
import httpx

BASE_URL = "http://localhost:8080"


async def test_api_endpoints():
    """Test all CRUDL endpoints."""
    async with httpx.AsyncClient() as client:
        print("🚀 Testing API endpoints...")

        # Test health check
        print("\n📋 Testing health check...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"Health check: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Health check failed: {e}")

        # Test Users CRUDL
        print("\n👤 Testing Users CRUDL...")
        user_id = None
        try:
            # Create user
            user_data = {"name": "Test User", "email": "test@example.com"}
            response = await client.post(f"{BASE_URL}/users", json=user_data)
            print(f"Create user: {response.status_code}")
            if response.status_code == 201:
                user = response.json()
                user_id = user["id"]
                print(f"Created user ID: {user_id}")

            # List users
            response = await client.get(f"{BASE_URL}/users")
            print(f"List users: {response.status_code}")

            # Get specific user
            if user_id:
                response = await client.get(f"{BASE_URL}/users/{user_id}")
                print(f"Get user: {response.status_code}")

                # Update user
                updated_user_data = {"name": "Updated Test User", "email": "updated@example.com"}
                response = await client.put(f"{BASE_URL}/users/{user_id}", json=updated_user_data)
                print(f"Update user: {response.status_code}")

        except Exception as e:
            print(f"Users test failed: {e}")

        # Test Projects CRUDL
        print("\n📁 Testing Projects CRUDL...")
        project_id = None
        try:
            # Create project
            project_data = {"name": "Test Project", "description": "A test project"}
            response = await client.post(f"{BASE_URL}/projects", json=project_data)
            print(f"Create project: {response.status_code}")
            if response.status_code == 201:
                project = response.json()
                project_id = project["id"]
                print(f"Created project ID: {project_id}")

            # List projects
            response = await client.get(f"{BASE_URL}/projects")
            print(f"List projects: {response.status_code}")

        except Exception as e:
            print(f"Projects test failed: {e}")

        # Test Agent Profiles CRUDL
        print("\n🤖 Testing Agent Profiles CRUDL...")
        profile_id = None
        try:
            # Create agent profile
            profile_data = {"name": "Test Agent", "instructions": ["Be helpful", "Be concise"]}
            response = await client.post(f"{BASE_URL}/agent-profiles", json=profile_data)
            print(f"Create agent profile: {response.status_code}")
            if response.status_code == 201:
                profile = response.json()
                profile_id = profile["id"]
                print(f"Created profile ID: {profile_id}")

            # List agent profiles
            response = await client.get(f"{BASE_URL}/agent-profiles")
            print(f"List agent profiles: {response.status_code}")

            # Test instructions within agent profile
            if profile_id:
                # Add instruction
                instruction_data = {"content": "Always verify information"}
                response = await client.post(
                    f"{BASE_URL}/agent-profiles/{profile_id}/instructions", json=instruction_data
                )
                print(f"Add instruction: {response.status_code}")

                # List instructions
                response = await client.get(f"{BASE_URL}/agent-profiles/{profile_id}/instructions")
                print(f"List instructions: {response.status_code}")

        except Exception as e:
            print(f"Agent profiles test failed: {e}")

        # Test Conversations CRUDL
        print("\n💬 Testing Conversations CRUDL...")
        if user_id and project_id and profile_id:
            try:
                # Create conversation
                conversation_data = {"project_id": project_id, "user_id": user_id, "agent_profile_id": profile_id}
                response = await client.post(f"{BASE_URL}/conversations", json=conversation_data)
                print(f"Create conversation: {response.status_code}")
                if response.status_code == 201:
                    conversation = response.json()
                    conversation_id = conversation["id"]
                    print(f"Created conversation ID: {conversation_id}")

                    # Add message to conversation
                    message_data = {"role": "user", "content": "Hello, this is a test message"}
                    response = await client.post(
                        f"{BASE_URL}/conversations/{conversation_id}/messages", json=message_data
                    )
                    print(f"Add message: {response.status_code}")

                # List conversations
                response = await client.get(f"{BASE_URL}/conversations")
                print(f"List conversations: {response.status_code}")

            except Exception as e:
                print(f"Conversations test failed: {e}")

        # Cleanup - delete created resources
        print("\n🧹 Cleaning up...")
        try:
            if user_id:
                response = await client.delete(f"{BASE_URL}/users/{user_id}")
                print(f"Delete user: {response.status_code}")
        except Exception as e:
            print(f"Cleanup failed: {e}")

        print("\n✅ API endpoint testing completed!")


if __name__ == "__main__":
    asyncio.run(test_api_endpoints())
