"""School service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, List, Optional
from logger_config import get_logger
from routes import school_db_url
from helpers import (
    db_request_token,
    is_response_valid,
    safe_get_first_item,
    is_response_empty,
)
from mapping import (
    SCHOOL_QUERY_PARAMS,
    USER_QUERY_PARAMS,
    states_for_auth_group,
)
from services.school_mapping_constants import (
    GUJARAT_DISTRICT_SCHOOL_MAPPING,
    STATE_DISTRICT_ALLOWLISTS,
)
from services.olf_school_allocation import OLF_SCHOOL_UDISE_CODES

from services.token_service import (
    invalid_verification_response,
    resolve_auth_group_name,
    tokens_for_record,
)

logger = get_logger()

DB_SERVICE_MAX_PAGE_SIZE = 10_000

# Canonical Tamil Nadu district list for the TN Govt Hiring Form.
# This is intentionally Tamil Nadu specific and removes duplicate DB spelling variants.
TAMIL_NADU_SCHOOL_DISTRICTS = [
    "Ariyalur",
    "Chengalpattu",
    "Chennai",
    "Coimbatore",
    "Cuddalore",
    "Dharmapuri",
    "Dindigul",
    "Erode",
    "Kallakurichi",
    "Kanchipuram",
    "Kanniyakumari",
    "Karur",
    "Krishnagiri",
    "Madurai",
    "Mayiladuthurai",
    "Nagapattinam",
    "Namakkal",
    "Perambalur",
    "Pudukkottai",
    "Ramanathapuram",
    "Ranipet",
    "Salem",
    "Sivagangai",
    "Tenkasi",
    "Thanjavur",
    "The Nilgiris",
    "Theni",
    "Thiruvallur",
    "Thiruvarur",
    "Thoothukkudi",
    "Tiruchirappalli",
    "Tirunelveli",
    "Tirupathur",
    "Tiruppur",
    "Tiruvannamalai",
    "Vellore",
    "Villupuram",
    "Virudhunagar",
]

MAHARASHTRA_SCHOOL_DISTRICTS = [
    "Bhandara",
    "Chandrapur",
    "Gadchiroli",
    "Gondia",
    "Nagpur Zp",
    "Wardha",
]


def is_school_allocated(school: Dict[str, Any], auth_group: Optional[str]) -> bool:
    """Whether a school is one the given auth group may enrol into.

    Single source of truth for the allocation filter. This used to be two
    inline copies of the same if/elif chain -- one in get_districts_by_filters
    and one in get_dependant_field_mapping_for_auth_group -- which had drifted:
    only the latter checked Gujarat at school level. Both now call this.

    Allocation is keyed off the school's own state rather than off the auth
    group, so a multi-state group gets each state's allocation applied.
    """
    district = school.get("district")
    if not district:
        return False

    if auth_group == "PunjabTeachers":
        return school.get("af_school_category") in ["SoE", "RSMS"]

    state = school.get("state")

    # OLF publishes its allocation per school rather than per district, so it
    # is matched on UDISE. The district allowlists below are AF's own, wider
    # allocation and would admit schools that are not part of the programme.
    if auth_group == "OLFStudents":
        allocated = OLF_SCHOOL_UDISE_CODES.get(state)
        if allocated is None:
            return False
        return str(school.get("udise_code") or "").strip() in allocated

    # Gujarat is allocated per school, not per district.
    if state == "Gujarat":
        return (
            district in GUJARAT_DISTRICT_SCHOOL_MAPPING
            and school.get("name") in GUJARAT_DISTRICT_SCHOOL_MAPPING[district]
        )

    allowed_districts = STATE_DISTRICT_ALLOWLISTS.get(state)
    if allowed_districts is not None:
        return district in allowed_districts

    # States with no allowlist are unrestricted.
    return True


def _fetch_schools_for_states(
    states: List[str], error_message: str
) -> Optional[List[Dict[str, Any]]]:
    """Fetch schools across one or more states, since DB Service filters by one."""
    all_schools = []
    for state in states:
        page = _get_all_schools({"state": state}, error_message)
        if page is None:
            return None
        all_schools.extend(page)
    return all_schools


def _get_all_schools(
    query_params: Dict[str, Any], error_message: str
) -> Optional[List[Dict[str, Any]]]:
    """Fetch every matching school page from DB Service."""
    schools = []
    offset = 0

    while True:
        response = requests.get(
            school_db_url,
            params={
                **query_params,
                "limit": DB_SERVICE_MAX_PAGE_SIZE,
                "offset": offset,
            },
            headers=db_request_token(),
        )

        if not is_response_valid(response, error_message):
            return None

        page = response.json()
        if not isinstance(page, list):
            page = [page] if page else []

        schools.extend(page)

        if len(page) < DB_SERVICE_MAX_PAGE_SIZE:
            return schools

        offset += len(page)


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


async def verify_school_comprehensive(
    code: str, query_params: Dict[str, Any]
) -> Dict[str, Any]:
    """Comprehensive school verification returning canonical identifiers."""
    logger.info(f"Verifying school with code: {code} and params: {query_params}")
    group_name = resolve_auth_group_name(
        query_params.get("auth_group"), query_params.get("auth_group_id")
    )
    invalid_response = invalid_verification_response(group_name, "school", code)

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
        return invalid_response

    # Verify all query parameters
    for key, value in query_params.items():
        if key in USER_QUERY_PARAMS:
            user_data = school_record.get("user", {})
            if not isinstance(user_data, dict):
                logger.warning(f"Invalid user data structure for school code: {code}")
                return invalid_response
            if user_data.get(key) != value:
                logger.info(f"User verification failed for key: {key}")
                return invalid_response

        elif key in SCHOOL_QUERY_PARAMS:
            if key == "code" and found_via_udise_code:
                logger.info("Skipping code verification - found via udise_code")
                continue
            if school_record.get(key) != value:
                logger.info(f"School verification failed for key: {key}")
                return invalid_response

    logger.info(f"School verification successful for code: {code}")
    identifiers: Dict[str, Any] = {
        "user_id": None,
        "display_id": None,
        "display_id_type": "school_code",
        "school_code": None,
    }

    school_code = school_record.get("code") or code
    if school_code is not None:
        identifiers["display_id"] = str(school_code)
        identifiers["school_code"] = str(school_code)

    user_data = school_record.get("user", {})
    if isinstance(user_data, dict):
        user_pk = user_data.get("id")
        if user_pk is not None:
            identifiers["user_id"] = str(user_pk)

    identifiers = {k: v for k, v in identifiers.items() if v is not None}
    return {
        "is_valid": True,
        **identifiers,
        **tokens_for_record(school_record, "school", identifiers, group_name),
    }


def get_districts_by_filters(
    auth_group: Optional[str] = None, state: Optional[str] = None
) -> Dict[str, Any]:
    """Get list of unique districts, filtered by auth_group or state."""
    # An explicit state wins over the auth group's own states, so a multi-state
    # group can ask for the districts of the one state the student picked.
    if state:
        states = [state]
    elif auth_group:
        states = states_for_auth_group(auth_group)
    else:
        states = []

    if states == ["Tamil Nadu"]:
        return {"districts": TAMIL_NADU_SCHOOL_DISTRICTS}

    logger.info(f"Fetching districts for states: {states}, auth_group: {auth_group}")

    if states:
        schools_data = _fetch_schools_for_states(states, "Could not fetch districts!")
    else:
        schools_data = _get_all_schools({}, "Could not fetch districts!")

    if schools_data is not None:
        districts = sorted(
            school["district"]
            for school in schools_data
            if is_school_allocated(school, auth_group)
        )

        logger.info(f"Found {len(districts)} districts")
        return {"districts": districts}

    return {"districts": []}


def get_blocks_by_filters(
    auth_group: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
) -> Dict[str, Any]:
    """Get list of unique blocks, filtered by auth_group/state and district."""
    query_params = {}

    # An explicit state wins, so a multi-state auth group can scope to the one
    # state the student picked; otherwise fall back to the group's own state.
    if state:
        query_params["state"] = state
    elif auth_group:
        group_states = states_for_auth_group(auth_group)
        if len(group_states) == 1:
            query_params["state"] = group_states[0]

    if district:
        query_params["district"] = district

    logger.info(f"Fetching blocks with params: {query_params}")

    schools_data = _get_all_schools(
        query_params,
        "Could not fetch blocks!",
    )

    if schools_data is not None:
        # Extract unique blocks (block_name field)
        blocks = list(
            set(
                school.get("block_name")
                for school in schools_data
                if school.get("block_name") and is_school_allocated(school, auth_group)
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

    # An explicit state wins, so a multi-state auth group can scope to the one
    # state the student picked; otherwise fall back to the group's own state.
    if state:
        query_params["state"] = state
    elif auth_group:
        group_states = states_for_auth_group(auth_group)
        if len(group_states) == 1:
            query_params["state"] = group_states[0]

    if district:
        query_params["district"] = district

    if block:
        query_params["block_name"] = block

    logger.info(f"Fetching schools for dropdown with params: {query_params}")

    schools_data = _get_all_schools(
        query_params,
        "Could not fetch schools!",
    )

    if schools_data is not None:
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
            if school.get("name") and is_school_allocated(school, auth_group)
        ]

        # Sort by name
        schools.sort(key=lambda x: x["name"])

        logger.info(f"Found {len(schools)} schools")
        return {"schools": schools}

    return {"schools": []}


def get_dependant_field_mapping_for_auth_group(
    auth_group: str, include_blocks: bool = False, state: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate dependantFieldMapping for district->school or district->block->school hierarchy.
    This replaces manual google sheets and prevents data mismatches!

    Returns the exact structure needed for form schema dependantFieldMapping.

    `state` narrows a multi-state auth group to one state. Without it a
    multi-state group returns every state's districts merged together.
    """
    states = states_for_auth_group(auth_group)
    if not states:
        logger.warning(f"Unknown auth_group: {auth_group}")
        return {"error": "Invalid auth group"}

    if state:
        if state not in states:
            logger.warning(f"State '{state}' is not covered by auth group {auth_group}")
            return {"error": "Invalid state for auth group"}
        states = [state]

    logger.info(
        f"Generating dependant mapping for '{auth_group}' -> {states}, include_blocks: {include_blocks}"
    )

    schools_data = _fetch_schools_for_states(
        states,
        "Could not fetch schools for dependant mapping!",
    )

    if schools_data is None:
        return {"error": "Database error"}

    filtered_schools = [
        school for school in schools_data if is_school_allocated(school, auth_group)
    ]

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

            # Every allocated school is expected to carry a block. Skipping the
            # rare one that does not is safer than inventing a placeholder
            # block name, which would show students a block that exists in no
            # government data.
            if not block:
                continue

            if block not in district_block_mapping[district]["en"]:
                district_block_mapping[district]["en"].append(block)
                district_block_mapping[district]["hi"].append(block)

            # Build block -> schools mapping
            if block not in block_school_mapping:
                block_school_mapping[block] = {"en": [], "hi": []}

            if school_name not in block_school_mapping[block]["en"]:
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
            "state": states[0] if len(states) == 1 else None,
            "states": states,
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

            if school_name not in district_school_mapping[district]["en"]:
                district_school_mapping[district]["en"].append(school_name)
                district_school_mapping[district]["hi"].append(school_name)

        # Sort everything
        for district_data in district_school_mapping.values():
            district_data["en"].sort()
            district_data["hi"].sort()

        return {
            "auth_group": auth_group,
            "state": states[0] if len(states) == 1 else None,
            "states": states,
            "has_blocks": False,
            "district_school_mapping": district_school_mapping,
        }
