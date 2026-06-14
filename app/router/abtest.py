from fastapi import APIRouter, HTTPException, Request
import json
from pathlib import Path
from helpers import validate_and_build_query_params
from services.session_service import get_session_by_id
from logger_config import get_logger

logger = get_logger()

router = APIRouter(prefix="/abtest", tags=["ABTest"])


@router.get("/")
async def get_ab_test_data(request: Request):
    try:
        # query_params = validate_and_build_query_params(request.query_params, ["id"])
        # file_path = Path(f"public/abtests/{query_params['id']}.json")
        # Accept both 'id' (required) and 'session_type' (optional) query parameters
        allowed_params = ["id", "session_type"]
        query_params = validate_and_build_query_params(request.query_params, allowed_params)
        
        test_id = query_params["id"]
        session_type = query_params.get("session_type")
        
        file_path = Path(f"public/abtests/{test_id}.json")
        if not file_path.exists():
            raise HTTPException(
                status_code=404, detail=f"A/B test with ID {test_id} not found"
            )

        with open(file_path, "r") as file:
            ab_test_data = json.load(file)
        
        if session_type and "session_ids" in ab_test_data:
            filtered_session_ids = []
            for session_id in ab_test_data["session_ids"]:
                try:
                    session = await get_session_by_id(session_id)
                    if session and session.get("type") == session_type:
                        filtered_session_ids.append(session_id)
                except Exception as e:
                    logger.warning(f"Could not fetch session {session_id}: {str(e)}")
                    # Continue with other sessions even if one fails
                    continue
            
            # Updates the AB test data with filtered session IDs
            ab_test_data["session_ids"] = filtered_session_ids
            logger.info(f"Filtered AB test {test_id} by session_type '{session_type}': {len(filtered_session_ids)} sessions match")

        logger.info(f"Returning AB test data for {test_id}")
        return ab_test_data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error parsing A/B test data")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving A/B test data: {str(e)}"
        )
