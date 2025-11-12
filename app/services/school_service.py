"""School service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from logger_config import get_logger
from routes import school_db_url
from helpers import (
    db_request_token,
    is_response_valid,
    safe_get_first_item,
    is_response_empty,
)
from mapping import SCHOOL_QUERY_PARAMS, USER_QUERY_PARAMS, authgroup_state_mapping

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
    logger.info("Directly returning fixed states list")

    states = [
        "Andaman and Nicobar Islands",
        "Andhra Pradesh",
        "Arunachal Pradesh",
        "Assam",
        "Bihar",
        "Chandigarh",
        "Chhattisgarh",
        "Dadra and Nagar Haveli",
        "Daman and Diu",
        "Delhi",
        "Goa",
        "Gujarat",
        "Haryana",
        "Himachal Pradesh",
        "Jammu and Kashmir",
        "Jharkhand",
        "Karnataka",
        "Kerala",
        "Ladakh",
        "Lakshadweep",
        "Madhya Pradesh",
        "Maharashtra",
        "Manipur",
        "Meghalaya",
        "Mizoram",
        "Nagaland",
        "Odisha",
        "Puducherry",
        "Punjab",
        "Rajasthan",
        "Sikkim",
        "Tamil Nadu",
        "Telangana",
        "Tripura",
        "Uttar Pradesh",
        "Uttarakhand",
        "West Bengal",
    ]
    states.sort()

    return {"states": states}


async def verify_school_comprehensive(code: str, query_params: Dict[str, Any]) -> bool:
    """Comprehensive school verification with fallback logic."""
    logger.info(f"Verifying school with code: {code} and params: {query_params}")

    # Try school code first
    school_record = None
    found_via_udise_code = False

    response = requests.get(
        school_db_url,
        params={"code": code},
        headers=db_request_token(),
    )

    if is_response_valid(response):
        data = is_response_empty(response.json(), False)
        if data:
            school_record = (
                safe_get_first_item(data) if isinstance(data, list) else data
            )

    # If no school found with school code, try udise_code
    if not school_record:
        logger.info(f"No school found with code, trying udise_code for: {code}")

        response = requests.get(
            school_db_url,
            params={"udise_code": code},
            headers=db_request_token(),
        )

        if is_response_valid(response):
            data = is_response_empty(response.json(), False)
            if data:
                school_record = (
                    safe_get_first_item(data) if isinstance(data, list) else data
                )
                found_via_udise_code = True

    if not school_record:
        logger.warning(f"No school found for code: {code}")
        return False

    # Verify all query parameters
    for key, value in query_params.items():
        if key in USER_QUERY_PARAMS:
            user_data = school_record.get("user", {})
            if not isinstance(user_data, dict):
                logger.warning(f"Invalid user data structure for school code: {code}")
                return False
            if user_data.get(key) != value:
                logger.info(f"User verification failed for key: {key}")
                return False

        elif key in SCHOOL_QUERY_PARAMS:
            if key == "code" and found_via_udise_code:
                logger.info("Skipping code verification - found via udise_code")
                continue
            if school_record.get(key) != value:
                logger.info(f"School verification failed for key: {key}")
                return False

    logger.info(f"School verification successful for code: {code}")
    return True


def get_districts_by_filters(
    auth_group: Optional[str] = None, state: Optional[str] = None
) -> Dict[str, Any]:
    """Get list of unique districts, filtered by auth_group or state."""
    query_params = {}

    # If auth_group provided, map to state
    if auth_group and auth_group in authgroup_state_mapping:
        query_params["state"] = authgroup_state_mapping[auth_group]
        logger.info(
            f"Mapped auth_group '{auth_group}' to state '{query_params['state']}'"
        )
    elif state:
        query_params["state"] = state

    logger.info(f"Fetching districts with params: {query_params}")

    response = requests.get(
        school_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Could not fetch districts!"):
        schools_data = response.json()
        if not isinstance(schools_data, list):
            schools_data = [schools_data]

        districts = []
        chhattisgarh_districts = "Bastar+DANTEWADA+Dhamtari+Durg+Gariaband+Janjgir - Champa+Jashpur+Raigarh+Raipur+Rajnandgaon".split(
            "+"
        )
        maharashtra_districts = ["Gadchiroli", "Bhandara"]
        for school in schools_data:
            if school.get("district"):
                if auth_group == "PunjabTeachers":
                    if school.get("af_school_category") in ["SoE", "RSMS"]:
                        districts.append(school.get("district"))
                elif auth_group == "ChhattisgarhStudents":
                    if school.get("district") in chhattisgarh_districts:
                        districts.append(school.get("district"))  # change later
                elif auth_group == "MaharashtraStudents":
                    if school.get("district") in maharashtra_districts:
                        districts.append(school.get("district"))  # change later
                else:
                    districts.append(school.get("district"))

        districts.sort()

        logger.info(f"Found {len(districts)} unique districts")
        return {"districts": districts}

    return {"districts": []}


def get_blocks_by_filters(
    auth_group: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
) -> Dict[str, Any]:
    """Get list of unique blocks, filtered by auth_group/state and district."""
    query_params = {}

    # If auth_group provided, map to state
    if auth_group and auth_group in authgroup_state_mapping:
        query_params["state"] = authgroup_state_mapping[auth_group]
    elif state:
        query_params["state"] = state

    if district:
        query_params["district"] = district

    logger.info(f"Fetching blocks with params: {query_params}")

    response = requests.get(
        school_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Could not fetch blocks!"):
        schools_data = response.json()
        if not isinstance(schools_data, list):
            schools_data = [schools_data]

        # Extract unique blocks (block_name field)
        blocks = list(
            set(
                school.get("block_name")
                for school in schools_data
                if school.get("block_name")
            )
        )
        blocks.sort()

        logger.info(f"Found {len(blocks)} unique blocks")
        return {"blocks": blocks}

    return {"blocks": []}


def get_schools_for_dropdown_by_filters(
    auth_group: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
    block: Optional[str] = None,
) -> Dict[str, Any]:
    """Get list of schools for dropdown, filtered by location hierarchy."""
    query_params = {}

    # If auth_group provided, map to state
    if auth_group and auth_group in authgroup_state_mapping:
        query_params["state"] = authgroup_state_mapping[auth_group]
    elif state:
        query_params["state"] = state

    if district:
        query_params["district"] = district

    if block:
        query_params["block_name"] = block

    logger.info(f"Fetching schools for dropdown with params: {query_params}")

    response = requests.get(
        school_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Could not fetch schools!"):
        schools_data = response.json()
        if not isinstance(schools_data, list):
            schools_data = [schools_data]

        # Return simplified school data for dropdown
        schools = [
            {
                "id": school.get("id"),
                "name": school.get("name"),
                "code": school.get("code"),
                "district": school.get("district"),
                "block_name": school.get("block_name"),
            }
            for school in schools_data
            if school.get("name")
        ]

        # Sort by name
        schools.sort(key=lambda x: x["name"])

        logger.info(f"Found {len(schools)} schools")
        return {"schools": schools}

    return {"schools": []}


def get_dependant_field_mapping_for_auth_group(
    auth_group: str, include_blocks: bool = False
) -> Dict[str, Any]:
    """
    Generate dependantFieldMapping for district->school or district->block->school hierarchy.
    This replaces manual google sheets and prevents data mismatches!

    Returns the exact structure needed for form schema dependantFieldMapping.
    """
    if auth_group not in authgroup_state_mapping:
        logger.warning(f"Unknown auth_group: {auth_group}")
        return {"error": "Invalid auth group"}

    state = authgroup_state_mapping[auth_group]
    logger.info(
        f"Generating dependant mapping for '{auth_group}' -> '{state}', include_blocks: {include_blocks}"
    )

    # Single API call to get all schools for this state
    response = requests.get(
        school_db_url, params={"state": state}, headers=db_request_token()
    )

    if not is_response_valid(
        response, "Could not fetch schools for dependant mapping!"
    ):
        return {"error": "Database error"}

    schools_data = response.json()
    if not isinstance(schools_data, list):
        schools_data = [schools_data]

    # Apply same filtering logic as get_districts_by_filters for consistency
    filtered_schools = []
    chhattisgarh_districts = "Bastar+DANTEWADA+Dhamtari+Durg+Gariaband+Janjgir - Champa+Jashpur+Raigarh+Raipur+Rajnandgaon".split(
        "+"
    )
    maharashtra_districts = ["Gadchiroli", "Bhandara"]
    for school in schools_data:
        if school.get("district"):
            if auth_group == "PunjabTeachers":
                if school.get("af_school_category") in ["SoE", "RSMS"]:
                    filtered_schools.append(school)
            elif auth_group == "ChhattisgarhStudents":
                if school.get("district") in chhattisgarh_districts:
                    filtered_schools.append(school)
            elif auth_group == "MaharashtraStudents":
                if school.get("district") in maharashtra_districts:
                    filtered_schools.append(school)
            else:
                filtered_schools.append(school)

    if include_blocks:
        # District -> Block -> School hierarchy
        district_block_mapping = {}
        block_school_mapping = {}

        for school in filtered_schools:
            district = school.get("district")
            block = school.get("block_name")
            school_name = school.get("name")

            if not district or not school_name:
                continue

            # Build district -> blocks mapping
            if district not in district_block_mapping:
                district_block_mapping[district] = {"en": [], "hi": []}

            if block:
                if block not in district_block_mapping[district]["en"]:
                    district_block_mapping[district]["en"].append(block)
                    district_block_mapping[district]["hi"].append(block)

                # Build block -> schools mapping
                if block not in block_school_mapping:
                    block_school_mapping[block] = {"en": [], "hi": []}

                block_school_mapping[block]["en"].append(school_name)
                block_school_mapping[block]["hi"].append(school_name)

        # Sort everything
        for district_data in district_block_mapping.values():
            district_data["en"].sort()
            district_data["hi"].sort()
        for block_data in block_school_mapping.values():
            block_data["en"].sort()
            block_data["hi"].sort()

        return {
            "auth_group": auth_group,
            "state": state,
            "has_blocks": True,
            "district_block_mapping": district_block_mapping,
            "block_school_mapping": block_school_mapping,
        }

    else:
        # Simple District -> School hierarchy
        district_school_mapping = {}

        for school in filtered_schools:
            district = school.get("district")
            school_name = school.get("name")

            if not district or not school_name:
                continue

            if district not in district_school_mapping:
                district_school_mapping[district] = {"en": [], "hi": []}

            district_school_mapping[district]["en"].append(school_name)
            district_school_mapping[district]["hi"].append(school_name)

        # Sort everything
        for district_data in district_school_mapping.values():
            district_data["en"].sort()
            district_data["hi"].sort()

        return {
            "auth_group": auth_group,
            "state": state,
            "has_blocks": False,
            "district_school_mapping": district_school_mapping,
        }
