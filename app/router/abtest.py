from fastapi import APIRouter, HTTPException, Request
import json
from pathlib import Path
from helpers import validate_and_build_query_params

router = APIRouter(prefix="/abtest", tags=["ABTest"])


@router.get("/")
def get_ab_test_data(request: Request):
    try:
        query_params = validate_and_build_query_params(request.query_params, ["id"])
        file_path = Path(f"public/abtests/{query_params['id']}.json")
        if not file_path.exists():
            raise HTTPException(
                status_code=404, detail=f"A/B test with ID {id} not found"
            )
        with open(file_path, "r") as file:
            ab_test_data = json.load(file)
        return ab_test_data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error parsing A/B test data")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving A/B test data: {str(e)}"
        )
