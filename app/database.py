from app.models import Customer,Claim,Policy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import asc, desc
from app.db import SessionLocal
from datetime import datetime
from app.models import Claim, Policy, Customer
from app.logger import logger

DATABASE_URL = "sqlite:///insurance.db"


def insert_customers(records):

    session = SessionLocal()

    inserted = 0
    rejected = 0
    errors = []

    for row in records:

        customer = Customer(
            customer_id=row["customer_id"],
            name=row["name"],
            age=int(row["age"]),
            city=row["city"],
            state=row["state"]
        )

        try:
            session.add(customer)
            session.commit()
            inserted += 1
            logger.info(
    f"Customer inserted successfully: {row['customer_id']}"
)

        except IntegrityError as e:
            logger.warning(
    f"Customer insert failed: {row['customer_id']} | {e.orig}"
)
            session.rollback()
            rejected += 1

            if "UNIQUE" in str(e.orig):
                errors.append("Duplicate Customer ID")
            else:
                errors.append(str(e.orig))

    session.close()

    return {
        "inserted": inserted,
        "rejected": rejected,
        "errors": errors
    }

def insert_policies(records):

    session = SessionLocal()

    inserted = 0
    rejected = 0
    errors = []

    for row in records:

        policy = Policy(
            policy_id=row["policy_id"],
            customer_id=row["customer_id"],
            policy_issue_date=datetime.strptime(
        row["policy_issue_date"],
        "%Y-%m-%d"
    ).date(),
            coverage_limit=float(row["coverage_limit"]),
            deductible=float(row["deductible"]),
            state=row["state"]
        )

        try:
            session.add(policy)
            session.commit()
            inserted += 1
            logger.info(
    f"Policy inserted successfully: {row['policy_id']}"
)

        except IntegrityError as e:
            logger.warning(
    f"Policy insert failed: {row['policy_id']} | {e.orig}"
)

            session.rollback()
            rejected += 1

            message = str(e.orig)

            if "FOREIGN KEY" in message:
                errors.append("Customer not found")

            elif "UNIQUE" in message:
                errors.append("Duplicate Policy ID")

            elif "CHECK" in message:
                errors.append("Constraint validation failed")

            else:
                errors.append(message)

    session.close()

    return {
        "inserted": inserted,
        "rejected": rejected,
        "errors": errors
    }

def insert_claims(records):

    session = SessionLocal()

    inserted = 0
    rejected = 0
    errors = []

    for row in records:

        # Check whether the policy exists
        policy = session.query(Policy).filter(
            Policy.policy_id == row["policy_id"]
        ).first()

        if policy is None:
            logger.warning(
                f"Claim rejected: {row['claim_id']} - Policy not found"
            )
            rejected += 1
            errors.append("Policy not found")
            continue

        # Convert claim date
        claim_date = datetime.strptime(
            row["loss_date"],
            "%Y-%m-%d"
        ).date()

        # Business Rule 3
        if claim_date < policy.policy_issue_date:
            logger.warning(
                f"Claim rejected: {row['claim_id']} - Claim date earlier than policy issue date"
            )

            rejected += 1
            errors.append("Claim date cannot be earlier than policy issue date")
            continue

        claim = Claim(
            claim_id=row["claim_id"],
            policy_id=row["policy_id"],
            loss_date=claim_date,
            loss_amount=float(row["loss_amount"]),
            cause=row["cause"]
        )

        try:
            session.add(claim)
            session.commit()
            inserted += 1
            logger.info(
    f"Claim inserted successfully: {row['claim_id']}"
)

        except IntegrityError as e:
            logger.warning(
    f"Claim insert failed: {row['claim_id']} | {e.orig}"
)
            session.rollback()
            rejected += 1

            if "FOREIGN KEY" in str(e.orig):
                errors.append("Policy not found")

            elif "UNIQUE" in str(e.orig):
                errors.append("Duplicate Claim ID")

            else:
                errors.append(str(e.orig))

    session.close()

    return {
        "inserted": inserted,
        "rejected": rejected,
        "errors": list(set(errors))
    }


# 8th rule fraud status

def get_fraud_status(session, customer_id):

    claim_count = (
        session.query(Claim)
        .join(Policy, Claim.policy_id == Policy.policy_id)
        .filter(Policy.customer_id == customer_id)
        .count()
    )

    if claim_count > 5:
        return 1

    return 0

# Calculate Payouts
def calculate_payout(claim, policy, customer):

    deductible = policy.deductible

    # Rule 7
    # Flood claims in California incur an additional 10% deductible
    if (
        claim.cause.lower() == "flood"
        and customer.state.upper() == "CA"
    ):
        deductible += deductible * 0.10

    # Rules 4 & 5
    payout = max(
        0,
        min(
            claim.loss_amount - deductible,
            policy.coverage_limit
        )
    )

    # Rule 6
    # Customers younger than 18 years receive only 50% payout
    if customer.age < 18:
        payout *= 0.5

    return round(payout, 2)



#get claim data by claim id
def get_claim_details(claim_id: str):
    logger.info(f"Fetching claim: {claim_id}")

    session = SessionLocal()

    claim = (
        session.query(Claim)
        .filter(Claim.claim_id == claim_id)
        .first()
    )

    if not claim:
        session.close()
        return None

    policy = (
        session.query(Policy)
        .filter(Policy.policy_id == claim.policy_id)
        .first()
    )

    customer = (
        session.query(Customer)
        .filter(Customer.customer_id == policy.customer_id)
        .first()
    )

    fraud_status = get_fraud_status(
    session,
    customer.customer_id
)

    # calc Payout
    payout = calculate_payout(claim, policy, customer)

    result = {
        "claim": {
            "claim_id": claim.claim_id,
            "loss_date": claim.loss_date,
            "loss_amount": claim.loss_amount,
            "cause": claim.cause
        },
        "policy": {
            "policy_id": policy.policy_id,
            "policy_issue_date": policy.policy_issue_date,
            "coverage_limit": policy.coverage_limit,
            "deductible": policy.deductible,
            "state": policy.state
        },
        "customer": {
            "customer_id": customer.customer_id,
            "name": customer.name,
            "age": customer.age,
            "city": customer.city,
            "state": customer.state
        },
        "calculated_payout": payout,
        **({"fraud_status": "Potential Fraud"} if fraud_status == 1 else {})
    }

    session.close()

    return result

#get claim details full

def get_claims(
    city=None,
    state=None,
    cause=None,
    start_date=None,
    end_date=None,
    min_payout=None,
    max_payout=None,
    sort_by="claim_id",
    order="asc"
):
    logger.info("Fetching all claims")
    session = SessionLocal()

    query = (
        session.query(Claim, Policy, Customer)
        .join(Policy, Claim.policy_id == Policy.policy_id)
        .join(Customer, Policy.customer_id == Customer.customer_id)
    )

    # ---------------- Filters ----------------

    if city:
        query = query.filter(Customer.city == city)

    if state:
        query = query.filter(Customer.state == state)

    if cause:
        query = query.filter(Claim.cause == cause)

    if start_date:
        query = query.filter(
            Claim.loss_date >= datetime.strptime(
                start_date,
                "%Y-%m-%d"
            ).date()
        )

    if end_date:
        query = query.filter(
            Claim.loss_date <= datetime.strptime(
                end_date,
                "%Y-%m-%d"
            ).date()
        )

    rows = query.all()

    results = []

    for claim, policy, customer in rows:

        fraud_status = get_fraud_status(
    session,
    customer.customer_id
)

        # calc Payout
        payout = calculate_payout(claim, policy, customer)

        if min_payout is not None and payout < min_payout:
            continue

        if max_payout is not None and payout > max_payout:
            continue

        results.append({
            "claim_id": claim.claim_id,
            "customer_name": customer.name,
            "city": customer.city,
            "state": customer.state,
            "policy_id": policy.policy_id,
            "loss_date": claim.loss_date,
            "loss_amount": claim.loss_amount,
            "cause": claim.cause,
            "payout": payout,
            **({"fraud_status": "Potential Fraud"} if fraud_status == 1 else {})
        })

    # ---------------- Sorting ----------------

    reverse = order.lower() == "desc"

    if sort_by in results[0] if results else []:
        results.sort(
            key=lambda x: x[sort_by],
            reverse=reverse
        )

    session.close()

    return {
        "total_records": len(results),
        "claims": results
    }

def get_top_customers(n):

    logger.info(f"Fetching top {n} customers")

    session = SessionLocal()

    query = (
        session.query(Customer, Policy, Claim)
        .join(Policy, Customer.customer_id == Policy.customer_id)
        .join(Claim, Policy.policy_id == Claim.policy_id)
        .all()
    )

    customer_payouts = {}

    for customer, policy, claim in query:

        # calc Payout
        payout = calculate_payout(claim, policy, customer)

        if customer.customer_id not in customer_payouts:

            fraud_status = get_fraud_status(
                session,
                customer.customer_id
                )            

            customer_payouts[customer.customer_id] = {
                "customer_id": customer.customer_id,
                "name": customer.name,
                "city": customer.city,
                "state": customer.state,
                "total_payout": 0,
                **({"fraud_status": "Potential Fraud"} if fraud_status == 1 else {})
            }

        customer_payouts[customer.customer_id]["total_payout"] += payout

    result = sorted(
        customer_payouts.values(),
        key=lambda x: x["total_payout"],
        reverse=True
    )

    session.close()

    return {
        "total_customers": min(n, len(result)),
        "customers": result[:n]
    }


def state_report():
    logger.info("Generating state report")

    session = SessionLocal()

    rows = (
        session.query(Customer, Policy, Claim)
        .join(Policy, Customer.customer_id == Policy.customer_id)
        .join(Claim, Policy.policy_id == Claim.policy_id)
        .all()
    )

    report = {}

    for customer, policy, claim in rows:

        # calc Payout
        payout = calculate_payout(claim, policy, customer)

        state = customer.state

        if state not in report:

            report[state] = {
                "state": state,
                "total_claims": 0,
                "total_payout": 0,
                "maximum_payout": 0
            }

        report[state]["total_claims"] += 1
        report[state]["total_payout"] += payout

        if payout > report[state]["maximum_payout"]:
            report[state]["maximum_payout"] = payout

    result = []

    for state, data in report.items():

        average = 0

        if data["total_claims"] > 0:
            average = data["total_payout"] / data["total_claims"]

        result.append({
            "state": state,
            "total_claims": data["total_claims"],
            "average_payout": round(average, 2),
            "maximum_payout": data["maximum_payout"],
            "total_payout": data["total_payout"]
        })

    session.close()

    return {
        "states": result
    }

def health_check(start_time):
    logger.info("Performing health check")

    try:
        session = SessionLocal()
        session.connection()   # If this succeeds, DB is connected

        database = "connected"
        status = "healthy"

    except Exception as e:
        logger.exception("Database health check failed")
        database = "disconnected"
        status = "unhealthy"

    finally:
        session.close()

    # Calculate uptime
    uptime = datetime.now() - start_time

    total_seconds = int(uptime.total_seconds())

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return {
    "status": status,
    "database": database,
    "uptime": f"{hours}h {minutes}m {seconds}s"
}


# raw sql query
from sqlalchemy import text

def top_cities_report():

    logger.info("Generating Top Cities report")

    session = SessionLocal()

    result = session.execute(text("""
        SELECT
            c.city,
            SUM(
                CASE
                    WHEN cl.loss_amount - p.deductible > p.coverage_limit
                        THEN p.coverage_limit
                    WHEN cl.loss_amount - p.deductible < 0
                        THEN 0
                    ELSE cl.loss_amount - p.deductible
                END
            ) AS total_payout

        FROM customer c
        JOIN policy p
            ON c.customer_id = p.customer_id
        JOIN claims cl
            ON p.policy_id = cl.policy_id

        GROUP BY c.city
        ORDER BY total_payout DESC
    """))

    return [dict(row._mapping) for row in result]

def claims_per_state_report():

    logger.info("Generating Claims Per State report")

    session = SessionLocal()

    try:

        query = text("""

            SELECT
                c.state,
                COUNT(cl.claim_id) AS total_claims

            FROM customer c

            INNER JOIN policy p
                ON c.customer_id = p.customer_id

            INNER JOIN claims cl
                ON p.policy_id = cl.policy_id

            GROUP BY c.state

            ORDER BY total_claims DESC

        """)

        result = session.execute(query)

        reports = []

        for row in result:

            reports.append({
                "state": row.state,
                "total_claims": row.total_claims
            })

        return {
            "total_states": len(reports),
            "reports": reports
        }

    finally:
        session.close()