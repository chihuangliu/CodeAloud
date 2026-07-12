from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import interview, code, questions

load_dotenv()

app = FastAPI(title="codeAloud API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://frontend:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview.router)
app.include_router(code.router)
app.include_router(questions.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
