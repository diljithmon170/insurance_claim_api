from fastapi import HTTPException

def validation_error(message):

    raise HTTPException(
        status_code=400,
        detail={
            "error": "ValidationError",
            "message": message
        }
    )


def not_found(message):

    raise HTTPException(
        status_code=404,
        detail={
            "error": "NotFound",
            "message": message
        }
    )


def conflict(message):

    raise HTTPException(
        status_code=409,
        detail={
            "error": "Conflict",
            "message": message
        }
    )