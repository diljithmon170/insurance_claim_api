from fastapi import FastAPI
from app.database.database import create_tables
from app.api.claim_routes import router

app = FastAPI(
    title="Insurance Claim API"
)


@app.on_event("startup")
def startup():
    create_tables()


app.include_router(router)


@app.get("/")
def home():
    return {"message": "Insurance Claim API"}