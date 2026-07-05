import os
import csv
from datetime import datetime, date
from fastapi import UploadFile, HTTPException
from app.exceptions import validation_error
from app.logger import logger

from app.database import (
    insert_customers,
    insert_policies,
    insert_claims
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class CSVService:

    async def save_file(self, file: UploadFile):

        logger.info(f"Uploading file: {file.filename}")

        if not file.filename.lower().endswith(".csv"):
            logger.warning(f"Invalid file uploaded: {file.filename}")
            validation_error("is not a CSV file")

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        logger.info(f"File saved successfully: {file.filename}")

        return file_path
    
    def clean_value(self, value):

        if value is None:
            return None

        value = str(value).strip()

        if value.lower() in ("", "null", "none", "na", "n/a"):
            return None

        return value

    def parse_date(self, value):

        if value is None:
            return None

        formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y/%m/%d"
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass

        return None

    async def process_csv(
        self,
        file: UploadFile,
        required_columns,
        unique_column,
        date_columns,
        numeric_columns
    ):

        file_path = await self.save_file(file)

        valid_records = []
        rejected_records = []
        seen = set()
        inserted = 0

        with open(file_path, "r", encoding="utf-8-sig") as csvfile:

            reader = csv.DictReader(csvfile)

            headers = reader.fieldnames or []

            missing = [
                col for col in required_columns
                if col not in headers
            ]

            if missing:
                logger.warning(
                    f"{file.filename} - Missing columns: {missing}"
                )
                validation_error("Missing columns")

            for row in reader:

                cleaned = {}

                # Clean whitespace / NULL values
                for key, value in row.items():
                    cleaned[key.strip()] = self.clean_value(value)

                # Duplicate check
                record_id = cleaned.get(unique_column)

                if record_id in seen:

                    logger.warning(
                        f"{file.filename} - Duplicate {unique_column}: {record_id}"
                    )

                    rejected_records.append({
                        "record": cleaned,
                        "error": f"Duplicate {unique_column}"
                    })

                    continue

                seen.add(record_id)

                # Date validation
                date_error = False

                for column in date_columns:

                    if cleaned.get(column):

                        parsed = self.parse_date(cleaned[column])

                        if parsed is None:

                            logger.warning(
                                f"{file.filename} - Invalid {column}: {cleaned.get(column)}"
                            )

                            rejected_records.append({
                                "record": cleaned,
                                "error": f"Invalid {column}"
                            })

                            date_error = True
                            break

                        # Check future date
                        parsed_date = datetime.strptime(parsed, "%Y-%m-%d").date()

                        if parsed_date > date.today():

                            logger.warning(
                                f"{file.filename} - Future {column}: {parsed}"
                            )

                            rejected_records.append({
                                "record": cleaned,
                                "error": f"{column} cannot be a future date"
                            })

                            date_error = True
                            break

                        cleaned[column] = parsed

                if date_error:
                    continue

                # Numeric validation
                number_error = False

                for column in numeric_columns:

                    if cleaned.get(column):

                        try:
                            cleaned[column] = float(cleaned[column])

                            # Amount should not be negative
                            if cleaned[column] < 0:

                                logger.warning(
                                    f"{file.filename} - Negative {column}: {cleaned[column]}"
                                )

                                rejected_records.append({
                                    "record": cleaned,
                                    "error": f"{column} cannot be negative"
                                })

                                number_error = True
                                break

                        except ValueError:

                            logger.warning(
                                f"{file.filename} - Invalid {column}: {cleaned.get(column)}"
                            )

                            rejected_records.append({
                                "record": cleaned,
                                "error": f"Invalid {column}"
                            })

                            number_error = True
                            break

                if number_error:
                    continue

                valid_records.append(cleaned)

        # Insert into database AFTER processing all rows
        logger.info(
            f"Starting database insertion for {file.filename}. "
            f"Valid records: {len(valid_records)}"
        )

        filename = file.filename.lower()
        db_result = None

        try:

            if "customer" in filename:
                db_result = insert_customers(valid_records)

            elif "policy" in filename:
                db_result = insert_policies(valid_records)

            elif "claim" in filename:
                db_result = insert_claims(valid_records)

        except Exception:

            logger.exception(
                f"Unexpected error while processing {file.filename}"
            )

            raise HTTPException(
                status_code=500,
                detail="Internal Server Error"
            )

        # Combine CSV validation errors and DB insertion errors
        errors = [record["error"] for record in rejected_records]
        errors.extend(db_result["errors"])

        # Upload summary
        logger.info(
            f"{file.filename} Upload Summary | "
            f"Total={len(valid_records) + len(rejected_records)} | "
            f"Inserted={db_result['inserted']} | "
            f"Rejected={len(rejected_records) + db_result['rejected']}"
        )

        return {
            "total_records": len(valid_records) + len(rejected_records),
            "inserted": db_result["inserted"],
            "rejected": len(rejected_records) + db_result["rejected"],
            "errors": list(set(errors))
        }