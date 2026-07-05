from fastapi import APIRouter, UploadFile, File, Query, Request
from typing import Optional
from app.services import CSVService
from app.database import *
from app.exceptions import not_found
from app.logger import logger


router = APIRouter(prefix="/api", tags=["CSV Upload"])


@router.post("/upload")
async def upload_csv_files(
    customer: UploadFile = File(...),
    policy: UploadFile = File(...),
    claims: UploadFile = File(...)
):

    logger.info("POST /api/upload called")

    service = CSVService()

    customer_result = await service.process_csv(
        file=customer,
        required_columns=[
            "customer_id",
            "name",
            "age",
            "city",
            "state"
        ],
        unique_column="customer_id",
        date_columns=[],
        numeric_columns=["age"]
    )

    policy_result = await service.process_csv(
        file=policy,
        required_columns=[
            "policy_id",
            "customer_id",
            "policy_issue_date",
            "coverage_limit",
            "deductible",
            "state"
        ],
        unique_column="policy_id",
        date_columns=["policy_issue_date"],
        numeric_columns=["coverage_limit", "deductible"]
    )

    claims_result = await service.process_csv(
        file=claims,
        required_columns=[
            "claim_id",
            "policy_id",
            "loss_date",
            "loss_amount",
            "cause"
        ],
        unique_column="claim_id",
        date_columns=["loss_date"],
        numeric_columns=["loss_amount"]
    )

    logger.info("CSV upload completed successfully")

    return {
        "customer": customer_result,
        "policy": policy_result,
        "claims": claims_result
    }


@router.get("/claims/{claim_id}")
def get_claim(claim_id: str):

    logger.info(f"GET /api/claims/{claim_id}")

    result = get_claim_details(claim_id)

    if result is None:
        logger.warning(f"Claim not found: {claim_id}")
        not_found("Claim not found")

    return result


@router.get("/claims")
def get_all_claims(
    city: Optional[str] = None,
    state: Optional[str] = None,
    cause: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_payout: Optional[float] = None,
    max_payout: Optional[float] = None,
    sort_by: Optional[str] = Query(
        "claim_id",
        description="claim_id, loss_date, payout, loss_amount"
    ),
    order: Optional[str] = Query(
        "asc",
        description="asc or desc"
    )
):

    logger.info("GET /api/claims")

    return get_claims(
        city,
        state,
        cause,
        start_date,
        end_date,
        min_payout,
        max_payout,
        sort_by,
        order
    )


@router.get("/customers/top")
def top_customers(n: int = Query(10, ge=1)):

    logger.info(f"GET /api/customers/top?n={n}")

    return get_top_customers(n)


@router.get("/reports/state")
def get_state_report():

    logger.info("GET /api/reports/state")

    return state_report()


@router.get("/health")
def health(request: Request):

    logger.info("GET /api/health")

    return health_check(request.app.state.start_time)


@router.get("/reports/top-cities")
def top_cities():

    logger.info("GET /api/reports/top-cities")

    return top_cities_report()


@router.get("/reports/claims-per-state")
def claims_per_state():

    logger.info("GET /api/reports/claims-per-state")

    return claims_per_state_report()