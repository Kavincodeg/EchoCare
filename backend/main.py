import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from database import connect_db, close_db
from routers import auth, tracker, story


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="EchoCare API",
    description="AI-Powered Healthcare Companion — FastAPI Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        frontend_url,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi import Request
from fastapi.responses import JSONResponse

@app.middleware("http")
async def allow_private_network(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as e:
        print("Exception in middleware:", e)
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"}
        )
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(tracker.router)
app.include_router(story.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "EchoCare API is running 🩺",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
