import pytest
import requests
import time
import os
import datetime
from jose import jwt
from dotenv import load_dotenv

BASE_URL = "http://127.0.0.1:8000"

@pytest.fixture
def valid_token():
    load_dotenv()
    secret_key = os.getenv('JWT_SECRET_KEY')
    payload = {
        "sub": "user",
        "exp": datetime.datetime.now(datetime.datetime.UTC) + datetime.timedelta(days=30)
    }
    token = jwt.encode(
        payload,
        secret_key,
        algorithm="HS256"
    )
    return token

def test_valid_imei_with_valid_token(valid_token):
    headers = {"Authorization": f"Bearer {valid_token}"}
    response = requests.get(
        f"{BASE_URL}/api/check-imei?imei=490154203237518",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "valid"
    assert data["imei"] == "490154203237518"
    assert data["details"].get('status', None) == "successful"

def test_invalid_imei_length(valid_token):
    headers = {"Authorization": f"Bearer {valid_token}"}
    response = requests.get(
        f"{BASE_URL}/api/check-imei?imei=1234",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "invalid"
    assert "15 digits" in data["message"]

def test_invalid_imei_characters(valid_token):
    headers = {"Authorization": f"Bearer {valid_token}"}
    response = requests.get(
        f"{BASE_URL}/api/check-imei?imei=49015420323751A",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "invalid"
    assert "must contain only digits" in data["message"]

def test_invalid_imei_checksum(valid_token):
    headers = {"Authorization": f"Bearer {valid_token}"}
    response = requests.get(
        f"{BASE_URL}/api/check-imei?imei=490154203237519",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "invalid"
    assert "checksum" in data["message"]

def test_no_token():
    response = requests.get(f"{BASE_URL}/api/check-imei?imei=490154203237518")
    assert response.status_code == 403
    assert "Not authenticated" in response.json()["detail"]

def test_invalid_token():
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(
        f"{BASE_URL}/api/check-imei?imei=490154203237518",
        headers=headers
    )
    assert response.status_code == 401
    assert "Invalid token" in response.json()["message"]

def test_malformed_token():
    headers = {"Authorization": "InvalidTokenFormat"}
    response = requests.get(
        f"{BASE_URL}/api/check-imei?imei=490154203237518",
        headers=headers
    )
    assert response.status_code == 403
    assert "Not authenticated" in response.json()["detail"]

def test_empty_imei(valid_token):
    headers = {"Authorization": f"Bearer {valid_token}"}
    response = requests.get(
        f"{BASE_URL}/api/check-imei?imei=",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "invalid"
    assert "empty" in data["message"].lower()

def test_missing_imei_parameter(valid_token):
    headers = {"Authorization": f"Bearer {valid_token}"}
    response = requests.get(
        f"{BASE_URL}/api/check-imei",
        headers=headers
    )
    assert response.status_code == 422
