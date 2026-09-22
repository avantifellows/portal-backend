"""Static school allowlists used for portal form option filtering."""

# DB-canonical school names verified against school.code/udise_code from the
# Gujarat portal form mapping sheet. Keep values aligned with public.school.name
# because registration validation uses school_name + district + state.
GUJARAT_DISTRICT_SCHOOL_MAPPING = {
    "Arvalli": ["EMRS Shamlaji-1", "EMRS Shamlaji-2", "Surya Sainik School Khrerncha"],
    "Banaskantha": [
        "EMRS Ambaji",
        "EMRS Amirgadh",
        "EMRS Jagana",
        "GLRS Jethi",
        "Model School Amirgadh",
    ],
    "Bharuch": ["EMRS JHAGADIYA ", "EMRS Waghalkhod"],
    "Chhotaudepur": [
        "EMRS Kawant",
        "EMRS Kawant (PPP)",
        "EMRS Puniyawant",
        "GLRS Bhikhapura",
        "GLRS Malaja",
        "GLRS Pisayata",
        "GLRS Saidivasan",
        "GLRS Tankhala",
        "Model School Chhotaudepur",
        "Model School Jetpur Pavi",
        "Model School Kawant",
        "Model School Nasvadi",
    ],
    "Dahod": [
        "EMRS Garbada",
        "EMRS Kharedi",
        "EMRS Lukhadiya",
        "EMRS Singhvad",
        "GLRS Khredi",
        "GLRS Nani Khajuri",
        "GLRS Ninamni Vav",
        "MS Limkheda",
        "Model school Dahod",
    ],
    "Dang": ["EMRS Ahwa", "EMRS Baripada", "EMRS Mahal", "EMRS Saputara"],
    "Mahisagar": ["EMRS Kadana", "EMRS Santrampur", "MS Santrampur"],
    "Narmada": [
        "EMRS DEDIYAPADA",
        "EMRS Nandod",
        "EMRS Tilakwada",
        "GLRS Dediyapada",
        "MS Dediyapada",
    ],
    "Navsari": ["EMRS Baratad"],
    "Panchmahal": ["EMRS Vejalpur", "GLRS Narukot"],
    "Sabarkantha": ["GLRS Khedbrma-2"],
    "Surat": ["EMRS Mangarol", "EMRS Mota", "Sainik School Bilwan"],
    "Tapi": ["EMRS Indu", "EMRS Khodada", "EMRS Ukai", "GLRS Babarghat-2"],
    "Vadodara": ["EMRS Goraj Waghodia-1", "EMRS Waghodiya-2"],
    "Valsad": ["EMRS Dharampur", "EMRS Kaprada", "EMRS Paradi"],
}


# District-level allowlists, one per state. These express "which schools in this
# state are ours to enrol" and were previously duplicated as inline literals in
# two separate filter blocks in school_service.py, which had already drifted
# apart. Keyed by state so a multi-state auth group (OLFStudents) can reuse the
# same allocation as the single-state groups.
#
# Gujarat is deliberately absent: it is the one state allocated at school level
# rather than district level, so it is filtered through
# GUJARAT_DISTRICT_SCHOOL_MAPPING above.
#
# TODO: this belongs on the school record in db-service as an allocation field
# rather than as a Python literal. Until that exists, adding a state or moving a
# district between AF and OLF means editing this file.
STATE_DISTRICT_ALLOWLISTS = {
    "Chhattisgarh": [
        "Bastar",
        "DANTEWADA",
        "Dhamtari",
        "Durg",
        "Gariaband",
        "Janjgir - Champa",
        "Jashpur",
        "Raigarh",
        "Raipur",
        "Rajnandgaon",
    ],
    "Bihar": ["Begusarai"],
    "Maharashtra": [
        "Bhandara",
        "Chandrapur",
        "Gadchiroli",
        "Gondia",
        "Nagpur Zp",
        "Wardha",
    ],
    # Balaghat is the only allocated MP district; its 261 schools carry
    # block_name, so MP drives the district -> block -> school hierarchy.
    "Madhya Pradesh": ["Balaghat"],
}
