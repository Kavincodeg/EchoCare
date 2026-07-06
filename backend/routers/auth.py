from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime
from database import get_db
from auth_utils import hash_password, verify_password, create_access_token, decode_token, verify_google_token

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str


class GoogleLoginRequest(BaseModel):
    id_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    active_plan: str


# ── Dependency ────────────────────────────────────────────────────────────────

async def get_current_user(token: str = Depends(oauth2_scheme)):
    db = get_db()
    email = decode_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserResponse)
async def register(data: RegisterRequest):
    db = get_db()
    existing = await db.users.find_one({"email": data.email.lower().strip()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    doc = {
        "email": data.email.lower().strip(),
        "full_name": data.full_name.strip(),
        "hashed_password": hash_password(data.password),
        "active_plan": "Free",
        "created_at": datetime.utcnow().isoformat(),
    }
    result = await db.users.insert_one(doc)

    return UserResponse(
        id=str(result.inserted_id),
        email=doc["email"],
        full_name=doc["full_name"],
        active_plan="Free",
    )


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_db()
    user = await db.users.find_one({"email": form_data.username.lower().strip()})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token({"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/google")
async def google_login(data: GoogleLoginRequest):
    payload = verify_google_token(data.id_token)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid Google ID token")

    email = payload.get("email").lower().strip()
    name = payload.get("name", "Google User").strip()

    db = get_db()
    user = await db.users.find_one({"email": email})

    if not user:
        doc = {
            "email": email,
            "full_name": name,
            "hashed_password": "",
            "active_plan": "Free",
            "created_at": datetime.utcnow().isoformat(),
        }
        result = await db.users.insert_one(doc)
        user = await db.users.find_one({"_id": result.inserted_id})

    token = create_access_token({"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        full_name=current_user["full_name"],
        active_plan=current_user.get("active_plan", "Free"),
    )
