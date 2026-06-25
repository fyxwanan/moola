import os
import time
import asyncio
from datetime import datetime

# Configure test database before imports
os.environ["DATABASE_NAME"] = "moola_test_db"

from fastapi.testclient import TestClient
from main import app

def teardown_test_db():
    print("Cleaning up test database...")
    from motor.motor_asyncio import AsyncIOMotorClient
    client_mongo = AsyncIOMotorClient("mongodb://localhost:27017")
    
    async def drop_db():
        await client_mongo.drop_database("moola_test_db")
        print("Test database dropped.")
        
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.ensure_future(drop_db())
    else:
        loop.run_until_complete(drop_db())

def test_bookkeeping_flow():
    # Wrap in with client block to trigger startup events (like MongoDB connection)
    with TestClient(app) as client:
        # 1. Register User A and User B with optional email fields
        print("\n1. Testing Register & Login (with Email)...")
        reg_response_a = client.post("/api/auth/register", json={
            "username": "usera_test",
            "password": "password123",
            "nickname": "测试用户A",
            "email": "usera@example.com"
        })
        assert reg_response_a.status_code == 200
        res_data_a = reg_response_a.json()
        token_a = res_data_a["access_token"]
        user_a_id = res_data_a["user"]["id"]
        assert res_data_a["user"]["email"] == "usera@example.com"
        print(f"Registered User A with email: {res_data_a['user']['email']}")

        reg_response_b = client.post("/api/auth/register", json={
            "username": "userb_test",
            "password": "password123",
            "nickname": "测试用户B",
            "email": "userb@example.com"
        })
        assert reg_response_b.status_code == 200
        res_data_b = reg_response_b.json()
        token_b = res_data_b["access_token"]
        user_b_id = res_data_b["user"]["id"]
        print(f"Registered User B with email: {res_data_b['user']['email']}")

        # 2. Test independent Upload API (POST and GET)
        print("\n2. Testing Standalone Upload API...")
        mock_image_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        upload_res = client.post(
            "/api/upload", 
            files={"file": ("avatar.png", mock_image_data, "image/png")}
        )
        assert upload_res.status_code == 200
        upload_data = upload_res.json()
        assert "url" in upload_data
        assert "id" in upload_data
        file_id = upload_data["id"]
        avatar_url = upload_data["url"]
        print(f"File uploaded successfully. Returned URL: {avatar_url}")
        
        # Test file download/serve API
        download_res = client.get(f"/api/upload/{file_id}")
        assert download_res.status_code == 200
        assert download_res.content == mock_image_data
        assert download_res.headers.get("content-type") == "image/png"
        assert download_res.headers.get("cache-control") == "public, max-age=31536000"
        etag = download_res.headers.get("etag")
        assert etag is not None
        print("Downloaded file matches uploaded mock image bytes and has caching and ETag headers.")
        
        # Test conditional request (If-None-Match) returning 304
        cond_res = client.get(f"/api/upload/{file_id}", headers={"If-None-Match": etag})
        assert cond_res.status_code == 304
        assert not cond_res.content
        print("Conditional GET request correctly returned 304 Not Modified.")

        # Update User A profile with the new avatar_url
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}
        
        profile_update = client.put("/api/auth/me", headers=headers_a, json={
            "avatar_url": avatar_url
        })
        assert profile_update.status_code == 200
        assert profile_update.json()["avatar_url"] == avatar_url
        print("Updated User A profile with cropped avatar URL successfully.")

        # 3. Verify Sliding Token Expiration Header
        print("\n3. Testing Sliding Token Refresh Header...")
        time.sleep(1) # wait 1 second to advance unix epoch second
        me_response = client.get("/api/auth/me", headers=headers_a)
        assert me_response.status_code == 200
        refreshed_token_header = me_response.headers.get("Authorization")
        assert refreshed_token_header is not None
        refreshed_token = refreshed_token_header.replace("Bearer ", "")
        assert refreshed_token != token_a
        headers_a = {"Authorization": f"Bearer {refreshed_token}"}
        print("Sliding window token refresh header verified.")

        # 4. Test Fuzzy Search User API (with debounced results representation)
        print("\n4. Testing Fuzzy Autocomplete User Search API...")
        # User A searches for "userb" (fuzzy username match)
        search_res = client.get("/api/users/search?q=userb", headers=headers_a)
        assert search_res.status_code == 200
        search_list = search_res.json()
        assert len(search_list) >= 1
        assert search_list[0]["username"] == "userb_test"
        assert search_list[0]["email"] == "userb@example.com"
        print(f"Fuzzy search by name resolved: {search_list[0]['nickname']} ({search_list[0]['email']})")

        # User A searches for "example.com" (fuzzy email match)
        search_res_email = client.get("/api/users/search?q=example.com", headers=headers_a)
        assert search_res_email.status_code == 200
        search_list_email = search_res_email.json()
        # Should return User B, but EXCLUDE User A (calling user is excluded)
        assert any(u["username"] == "userb_test" for u in search_list_email)
        assert not any(u["username"] == "usera_test" for u in search_list_email)
        print("Fuzzy search by email resolved. Requesting user exclusion verified.")

        # Empty search query returns recommended user list
        recommend_res = client.get("/api/users/search", headers=headers_a)
        assert recommend_res.status_code == 200
        recommend_list = recommend_res.json()
        assert len(recommend_list) >= 1
        assert not any(u["username"] == "usera_test" for u in recommend_list)
        print(f"Empty search query returned recommendation list. Count: {len(recommend_list)}")

        # 5. Test Categories & Ledgers
        print("\n5. Testing Category and Ledger Bookkeeping...")
        cat_list_res = client.get("/api/categories", headers=headers_a)
        cats = cat_list_res.json()
        system_expense_cat = [c for c in cats if c["type"] == "expense" and c["owner_id"] is None][0]
        
        # Create personal record
        rec_a_res = client.post("/api/records", headers=headers_a, json={
            "amount": 25.5,
            "type": "expense",
            "category_id": system_expense_cat["id"],
            "note": "日常消费",
            "record_date": datetime.utcnow().isoformat()
        })
        assert rec_a_res.status_code == 200
        print("Personal ledger transactions logic verified.")

        # Create shared project
        proj_res = client.post("/api/projects", headers=headers_a, json={
            "name": "合租账套"
        })
        assert proj_res.status_code == 200
        proj_id = proj_res.json()["id"]

        invite_res = client.post(f"/api/projects/{proj_id}/members", headers=headers_a, json={
            "username": "userb_test"
        })
        assert invite_res.status_code == 200

        rec_b_res = client.post("/api/records", headers=headers_b, json={
            "amount": 120.0,
            "type": "expense",
            "category_id": system_expense_cat["id"],
            "note": "分摊网费",
            "record_date": datetime.utcnow().isoformat(),
            "project_id": proj_id
        })
        assert rec_b_res.status_code == 200
        print("Project ledger transactions logic verified.")

        print("\n--- ALL BACKEND TEST CASES PASSED SUCCESSFULLY ---")

if __name__ == "__main__":
    try:
        test_bookkeeping_flow()
    finally:
        teardown_test_db()
