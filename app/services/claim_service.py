from app.database.database import get_connection


def create_claim(claim):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO claims (
            customer_name,
            policy_number,
            claim_amount,
            claim_type
        )
        VALUES (?, ?, ?, ?)
    """, (
        claim.customer_name,
        claim.policy_number,
        claim.claim_amount,
        claim.claim_type
    ))

    conn.commit()

    claim_id = cursor.lastrowid

    conn.close()

    return {
        "id": claim_id,
        "message": "Claim created successfully"
    }