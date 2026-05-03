import re, random, string


class ToolValidationError(Exception):
    def __init__(self, field: str, value, reason: str):
        self.field  = field
        self.value  = value
        self.reason = reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")


INITIAL_STATE = {
    "otp_sent": False,
    "otp_verified": False,
    "session_token": None,               # ATMA-TKN-XXXXXXXX
    "diagnosis_state": None,             # 'symptoms_provided'
    "issue_report_id": None,
    "consultation_id": None,
    "consultation_state": None,          # 'not_requested','requested','assigned','resolved'
    "grievance_id": None,
}


class StubContext:
    def __init__(self, state: dict):
        self.state    = state.copy()
        self.call_log = []

    def call(self, tool_name: str, **kwargs) -> dict:
        self.call_log.append({"tool": tool_name, "args": kwargs})
        if tool_name not in STUBS:
            raise ValueError(f"Unknown tool: {tool_name}")
        return STUBS[tool_name](self.state, **kwargs)

    def get_call_log(self) -> list:
        return self.call_log.copy()

    def reset(self, state: dict):
        self.state    = state.copy()
        self.call_log = []


def _validate_aadhaar(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{12}", v):
        raise ToolValidationError("aadhaar_number", v, "Must be exactly 12 digits")

def _validate_otp(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{6}", v):
        raise ToolValidationError("otp", v, "Must be exactly 6 digits")

def _validate_session(v):
    if not isinstance(v, str) or not re.fullmatch(r"ATMA-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match ATMA-TKN-XXXXXXXX")

def _gen_token():
    return "ATMA-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def _gen_id(prefix):
    return prefix + "".join(random.choices(string.digits, k=8))


def atma_generate_otp(state: dict, **kwargs) -> dict:
    """Sends OTP for ATMA authentication.
    Reads: nothing
    Mutates: otp_sent
    """
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    m = kwargs.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m):
        raise ToolValidationError("mobile_number", m, "Must be exactly 10 digits")
    state["otp_sent"] = True
    return {"status": "success", "message": "OTP sent to registered mobile number"}


def atma_verify_otp(state: dict, **kwargs) -> dict:
    """Verifies OTP and returns session_token.
    Reads: otp_sent
    Mutates: otp_verified, session_token
    """
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    _validate_otp(kwargs.get("otp"))
    if not state.get("otp_sent"):
        return {"status": "error", "code": "OTP_NOT_SENT", "message": "Call atma_generate_otp first."}
    token = _gen_token()
    state["otp_verified"] = True
    state["session_token"] = token
    return {"status": "success", "session_token": token}


def atma_get_crop_advisory(state: dict, **kwargs) -> dict:
    """Fetches crop-specific advisory for the location.
    Reads: session_token
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    return {
        "status": "success",
        "crop_type": kwargs.get("crop_type"),
        "location": kwargs.get("location"),
        "advisory": "Apply balanced fertilizer at sowing. Maintain optimal spacing. Monitor for pests after 30 days.",
    }


def atma_get_stage_based_advisory(state: dict, **kwargs) -> dict:
    """Provides growth-stage-specific recommendations.
    Reads: session_token
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    valid_stages = ("sowing", "germination", "vegetative", "flowering", "fruiting", "harvesting")
    gs = kwargs.get("growth_stage")
    if gs not in valid_stages:
        raise ToolValidationError("growth_stage", gs, f"Must be one of {valid_stages}")
    return {
        "status": "success",
        "crop_type": kwargs.get("crop_type"),
        "growth_stage": gs,
        "advisory": f"At {gs} stage: ensure adequate moisture and nutrient availability.",
    }


def atma_get_weather_based_advisory(state: dict, **kwargs) -> dict:
    """Generates advisory adjusted for weather conditions.
    Reads: session_token
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    return {
        "status": "success",
        "crop_type": kwargs.get("crop_type"),
        "location": kwargs.get("location"),
        "advisory": "Avoid spraying due to expected rainfall. Delay irrigation for 2 days.",
    }


def atma_report_crop_issue(state: dict, **kwargs) -> dict:
    """Reports a crop issue with symptoms.
    Reads: session_token
    Mutates: diagnosis_state, issue_report_id
    """
    _validate_session(kwargs.get("session_token"))
    valid_issues = ("pest", "disease", "nutrient_deficiency", "weather_damage")
    it = kwargs.get("issue_type")
    if it not in valid_issues:
        raise ToolValidationError("issue_type", it, f"Must be one of {valid_issues}")
    if not kwargs.get("symptoms"):
        return {"status": "error", "code": "EMPTY_SYMPTOMS", "message": "Symptoms description required."}
    rid = _gen_id("ATMA-ISS-")
    state["diagnosis_state"] = "symptoms_provided"
    state["issue_report_id"] = rid
    return {"status": "success", "issue_report_id": rid, "diagnosis_state": "symptoms_provided"}


def atma_diagnose_pest_disease(state: dict, **kwargs) -> dict:
    """Analyzes symptoms and returns diagnosis.
    Reads: session_token, diagnosis_state
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("diagnosis_state") != "symptoms_provided":
        return {"status": "error", "code": "NO_REPORT", "message": "Report crop issue first."}
    return {
        "status": "success",
        "issue_report_id": kwargs.get("issue_report_id"),
        "diagnosis": [{"name": "Stem Borer", "confidence": "high", "treatment": "Apply Chlorantraniliprole"}],
    }


def atma_get_fertilizer_recommendation(state: dict, **kwargs) -> dict:
    """Provides fertilizer recommendations.
    Reads: session_token
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    return {
        "status": "success",
        "crop_type": kwargs.get("crop_type"),
        "growth_stage": kwargs.get("growth_stage"),
        "recommendations": [
            {"fertilizer": "Urea", "quantity_kg_per_hectare": 130},
            {"fertilizer": "DAP", "quantity_kg_per_hectare": 50},
        ],
    }


def atma_get_irrigation_schedule(state: dict, **kwargs) -> dict:
    """Returns recommended irrigation schedule.
    Reads: session_token
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    return {
        "status": "success",
        "crop_type": kwargs.get("crop_type"),
        "location": kwargs.get("location"),
        "schedule": [
            {"day": 1, "action": "Light irrigation"},
            {"day": 7, "action": "Deep irrigation"},
        ],
    }


def atma_get_crop_plan(state: dict, **kwargs) -> dict:
    """Generates full-season crop plan.
    Reads: session_token
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    return {
        "status": "success",
        "crop_type": kwargs.get("crop_type"),
        "location": kwargs.get("location"),
        "milestones": [
            {"stage": "sowing", "week": 1},
            {"stage": "germination", "week": 2},
            {"stage": "vegetative", "week": 4},
            {"stage": "flowering", "week": 8},
            {"stage": "harvesting", "week": 16},
        ],
    }


def atma_request_expert_consultation(state: dict, **kwargs) -> dict:
    """Requests expert consultation.
    Reads: session_token
    Mutates: consultation_id, consultation_state
    """
    _validate_session(kwargs.get("session_token"))
    if not kwargs.get("issue_description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Issue description required."}
    cid = _gen_id("ATMA-CON-")
    state["consultation_id"] = cid
    state["consultation_state"] = "requested"
    return {"status": "success", "consultation_id": cid, "consultation_state": "requested"}


def atma_get_consultation_status(state: dict, **kwargs) -> dict:
    """Checks expert consultation status.
    Reads: session_token, consultation_state
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    return {
        "status": "success",
        "consultation_id": kwargs.get("consultation_id"),
        "consultation_state": state.get("consultation_state", "not_requested"),
    }


def atma_get_advisory_history(state: dict, **kwargs) -> dict:
    """Retrieves past advisories.
    Reads: session_token
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    return {
        "status": "success",
        "advisories": [{"date": "2024-06-15", "crop_type": "paddy", "advisory": "Apply zinc sulphate"}],
    }


def atma_raise_grievance(state: dict, **kwargs) -> dict:
    """Raises an ATMA grievance.
    Reads: session_token
    Mutates: grievance_id
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    valid_cats = ("incorrect_advisory", "no_advisory_available", "delayed_response", "expert_not_assigned", "irrelevant_recommendation")
    cat = kwargs.get("grievance_category")
    if cat not in valid_cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {valid_cats}")
    if not kwargs.get("description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description cannot be empty."}
    gid = _gen_id("ATMA-GRV-")
    state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}


def atma_track_grievance_status(state: dict, **kwargs) -> dict:
    """Tracks ATMA grievance status.
    Reads: session_token
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    gid = kwargs.get("grievance_id")
    if not gid:
        return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending", "remarks": None}


STUBS = {
    "atma_generate_otp": atma_generate_otp,
    "atma_verify_otp": atma_verify_otp,
    "atma_get_crop_advisory": atma_get_crop_advisory,
    "atma_get_stage_based_advisory": atma_get_stage_based_advisory,
    "atma_get_weather_based_advisory": atma_get_weather_based_advisory,
    "atma_report_crop_issue": atma_report_crop_issue,
    "atma_diagnose_pest_disease": atma_diagnose_pest_disease,
    "atma_get_fertilizer_recommendation": atma_get_fertilizer_recommendation,
    "atma_get_irrigation_schedule": atma_get_irrigation_schedule,
    "atma_get_crop_plan": atma_get_crop_plan,
    "atma_request_expert_consultation": atma_request_expert_consultation,
    "atma_get_consultation_status": atma_get_consultation_status,
    "atma_get_advisory_history": atma_get_advisory_history,
    "atma_raise_grievance": atma_raise_grievance,
    "atma_track_grievance_status": atma_track_grievance_status,
}
