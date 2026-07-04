# Python Developer Assignment
**Estimated Time:** 6–8 Hours  
**Submission Deadline:** Within 3 days of receiving the assignment

---

# Objective

Build a production-quality REST API for processing insurance claim data.

The objective is **not only to make the APIs work**, but also to demonstrate good software engineering practices, including:

- Clean project structure
- REST API design
- Data validation
- Business logic implementation
- Database design
- Error handling
- Logging
- Documentation

---

# Technology Stack

You may use **Flask(preferred)** or **FastAPI**.

Required libraries:

- Python 3.11+
- FastAPI / Flask
- SQLAlchemy
- SQLite (preferred) or PostgreSQL
- Pandas
- Pydantic (if using FastAPI)
- Logging module

Optional:

- Alembic
- Pytest
- Black
  
---

# Dataset

You are provided with three CSV files.

```
customer.csv
policy.csv
claims.csv
```

The data contains both valid and invalid records.

Your application should correctly process valid records while identifying and handling invalid ones.

---

# Database Schema

Design a relational database for the three datasets.

Your schema should maintain appropriate relationships between:

- Customers
- Policies
- Claims

Use appropriate:

- Primary keys
- Foreign keys
- Constraints

---

# Functional Requirements

---

## 1. Upload API

### Endpoint

```
POST /upload
```

### Description

Accept the three CSV files and import the data into the database.

### Requirements

Before inserting data:

- Validate required columns
- Validate data types
- Remove duplicate records
- Trim whitespace
- Handle NULL values
- Parse dates
- Validate relationships
- Store valid records
- Reject invalid records

### Response

Example:

```json
{
    "total_records": 1000,
    "inserted": 985,
    "rejected": 15,
    "errors": [
        "Duplicate Claim ID",
        "Policy not found",
        "Invalid date"
    ]
}
```

---

## 2. Get Claim Details

### Endpoint

```
GET /claims/{claim_id}
```

Return

- Claim information
- Customer information
- Policy information
- Calculated payout

---

## 3. Search Claims

### Endpoint

```
GET /claims
```

Support filtering by:

- City
- State
- Cause
- Date range
- Minimum payout
- Maximum payout

Support:

- Sorting

---

## 4. Top Customers

### Endpoint

```
GET /customers/top?n=10
```

Return customers having the highest total payouts.

---

## 5. State Report

### Endpoint

```
GET /reports/state
```

Return for each state:

- Total claims
- Average payout
- Maximum payout
- Total payout

---

## 6. Health Check

### Endpoint

```
GET /health
```

Verify

- API status
- Database connectivity

Example response:

```json
{
    "status": "healthy",
    "database": "connected",
    "uptime": "2h 13m"
}
```

---

# Business Rules
Implement the following business rules.

1. Loss amount cannot be negative.
2. Loss date cannot be in the future.
3. Claim date cannot be earlier than the policy issue date.
4. Final payout cannot exceed the policy coverage limit.
5. Final payout cannot be negative.
6. Customers younger than 18 years receive only **50% payout**.
7. Flood claims in California incur an additional **10% deductible**.
8. If a customer has more than **5 claims**, flag the customer as **Potential Fraud**.
9. Duplicate claims should not be inserted.
10. Policies referencing non-existing customers should be rejected.

---

# Pandas Requirements

Use Pandas to:

- Read CSV files
- Clean data
- Standardize column names
- Remove duplicates
- Convert dates
- Identify invalid rows
- Prepare clean data before database insertion

---

# SQL Requirements

Use SQLAlchemy for CRUD operations.

Additionally, write **at least two raw SQL queries** for reporting.

Examples:

- Top cities by payout
- Claims per state
- Average payout by cause

---

# Error Handling

Implement consistent API error responses.

Example:

```json
{
    "error": "ValidationError",
    "message": "Policy ID does not exist"
}
```

Use appropriate HTTP status codes.

Examples:

- 200
- 201
- 400
- 404
- 409
- 422
- 500

---

# Logging

Log the following:

- API requests
- Upload summary
- Validation failures
- Exceptions

Do **not** log sensitive information.

---

# API Documentation

If using FastAPI, Swagger documentation should be available.

Document each endpoint.


---

# README

Your README should include:

- Setup instructions
- Installation steps
- Running the project
- API endpoints
- Assumptions made
- Design decisions

---

# Bonus Features (Optional)

Additional credit will be given for:

- Alembic migrations
- Unit tests
- Integration tests
- Authentication
- Background tasks
- Async APIs
- Input schema validation
- Caching
- Rate limiting

---

# Submission

Submit:

- Source code
- README
- requirements.txt or pyproject.toml
- Database migration scripts (if any)

Do **not** submit:

- Virtual environments
- Database files
- Compiled binaries
- IDE configuration files

---

# Important Notes

- Focus on writing clean, maintainable code.
- Handle edge cases wherever applicable.
- Clearly document any assumptions.
- Code that works but cannot be explained during the interview will be evaluated accordingly.

Good luck!
