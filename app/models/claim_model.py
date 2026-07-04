from pydantic import BaseModel, Field


class Claim(BaseModel):
    customer_name: str = Field(..., min_length=3)
    policy_number: str
    claim_amount: float = Field(..., gt=0)
    claim_type: str