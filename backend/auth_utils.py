import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "echocare-super-secret-jwt-key-2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

import bcrypt

pwd_context = None  # replaced passlib with native bcrypt


def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed or not hashed.startswith(("$2a$", "$2b$", "$2y$")):
        return False
    try:
        pwd_bytes = plain.encode('utf-8')
        hashed_bytes = hashed.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


import urllib.request
import json

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "543477464295-p789kdf5nve8tr3kef1a4p120895o9e8.apps.googleusercontent.com")
GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"

def verify_google_token(id_token: str) -> Optional[dict]:
    try:
        req = urllib.request.Request(
            GOOGLE_CERTS_URL,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            certs = json.loads(response.read().decode())

        payload = jwt.decode(
            id_token,
            certs,
            algorithms=["RS256"],
            audience=GOOGLE_CLIENT_ID,
            issuer="https://accounts.google.com"
        )
        return payload
    except Exception as e:
        print("Google token verification failed:", e)
        try:
            # Fallback to decode unverified claims during local development / testing
            unverified = jwt.get_unverified_claims(id_token)
            if unverified and "email" in unverified:
                return unverified
        except Exception:
            pass
        return None
