from fastapi import FastAPI, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from typing import Union
from jose import jwt
import os
from dotenv import load_dotenv
import server.models as models
import requests

load_dotenv()

security = HTTPBearer()
app = FastAPI()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        secret_key = os.getenv('JWT_SECRET_KEY')
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "status": "invalid",
                "message": "Token has expired"
            }
        )
    except jwt.JWTError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "status": "invalid",
                "message": "Invalid token"
            }
        )
        
async def get_imei_details(imei: str):
    api_key = os.getenv('IMEI_API_KEY')
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept-Language': 'en',
        'Content-Type': 'application/json'
    }
    payload = {
        "deviceId": imei,
        "serviceId": 12
    }
    try:
        response = requests.post("https://api.imeicheck.net/v1/checks", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "invalid",
                "message": f"Error fetching IMEI details: {str(e)}"
            }
        )

@app.get("/api/check-imei")
async def check_imei(
    imei: str,
    token: Union[dict, JSONResponse] = Depends(verify_token)
):
    if isinstance(token, JSONResponse):
        return token
    
    try:
        phone_info = models.PhoneInfo(imei=imei)
        
        imei_details = await get_imei_details(imei)
        
        if isinstance(imei_details, JSONResponse):
            return imei_details
        
        return {
            "status": "valid",
            "imei": phone_info.imei,
            "message": "IMEI is valid",
            "user": token.get("sub"),
            "details": imei_details
        }
    except ValueError as e:
        return {
            "status": "invalid",
            "imei": imei,
            "message": e.errors()[0]['msg']
        }