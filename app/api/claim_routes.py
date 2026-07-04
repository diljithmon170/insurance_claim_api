from fastapi import APIRouter
from app.models.claim_model import Claim
from app.services.claim_service import create_claim

router = APIRouter()


@router.post("/claims")
def add_claim(claim: Claim):
    return create_claim(claim)