"""School service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from app.logger_config import get_logger
from app.routes import school_db_url
from app.helpers import db_request_token, is_response_valid, safe_get_first_item
from app.mapping import SCHOOL_QUERY_PARAMS

logger = get_logger()


def get_school_by_name_and_region(name: str, region: str) -> Optional[Dict[str, Any]]:
    """Get school by name and region."""
    return get_school(name=name, region=region)


def get_school_by_name_and_district(
    name: str, district: str
) -> Optional[Dict[str, Any]]:
    """Get school by name and district."""
    return get_school(name=name, district=district)


def get_school_by_name_district_state(
    name: str, district: str, state: str
) -> Optional[Dict[str, Any]]:
    """Get school by name, district, and state."""
    return get_school(name=name, district=district, state=state)


def get_school_by_code(code: str) -> Optional[Dict[str, Any]]:
    """Get school by code."""
    return get_school(code=code)


def get_school(**params) -> Optional[Dict[str, Any]]:
    """Get school with flexible parameters."""
    # Filter out None values and validate against allowed params
    query_params = {
        k: v for k, v in params.items() if v is not None and k in SCHOOL_QUERY_PARAMS
    }

    logger.info(f"Fetching school with params: {query_params}")

    response = requests.get(
        school_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "School API could not fetch the data!"):
        school_data = safe_get_first_item(response.json(), "School does not exist!")
        logger.info("Successfully retrieved school data")
        return school_data

    return None


def get_colleges_list() -> Dict[str, Any]:
    """Get list of colleges/universities for forms."""
    colleges = [
        "Central University of Kerala",
        "Delhi University",
        "Jadavpur University",
        "NIT Calicut",
        "NIT Delhi",
        "NIT Durgapur",
        "NIT Hamirpur",
        "NIT Jalandhar",
        "NIT Jamshedpur",
        "NIT Kurukshetra",
        "NIT Rourkela",
        "NIT Silchar",
        "NIT Srinagar",
        "NITK Surathkal",
        "NIT Trichy",
        "NIT Uttarakhand",
        "NIT Warangal",
        "SVNIT Surat",
        "IIT Jammu",
        "Hindu College Delhi",
        "PEC Chandigarh",
        "Central University of Karnataka",
        "Others",
    ]

    logger.info(f"Returning {len(colleges)} colleges")
    return {"colleges": colleges}


def get_states_list() -> Dict[str, Any]:
    """Get list of unique states from schools database."""
    logger.info("Fetching all unique states from schools database")

    response = requests.get(school_db_url, headers=db_request_token())

    if is_response_valid(response, "Could not fetch states from schools!"):
        schools_data = response.json()
        if not isinstance(schools_data, list):
            schools_data = [schools_data]

        # Extract unique states
        states = list(
            set(school.get("state") for school in schools_data if school.get("state"))
        )
        states.sort()

        logger.info(f"Found {len(states)} unique states from database")
        return {"states": states}

    return {"states": []}
