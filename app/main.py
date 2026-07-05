from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.models import create_tables
from app.routes import router
from datetime import datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()      # Runs once when the app starts
    yield                # Application runs here
    # Optional cleanup code here

app = FastAPI(
    title="Insurance Claim API",
    lifespan=lifespan
)

app.state.start_time = datetime.now()

app.include_router(router)