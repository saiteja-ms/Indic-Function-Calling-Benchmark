import re, random, string


class ToolValidationError(Exception):
    def __init__(self, field: str, value, reason: str):
        self.field  = field
        self.value  = value
        self.reason = reason
        super().__init__(
            f"Validation failed for '{field}': "
            f"{reason} (got: {value!r})"
        )


INITIAL_STATE = {
    "otp_sent": False,
    "otp_verified": False,
    "session_token": None,               # SHC-TKN-XXXXXXXX
    "sample_id": None,
    "sample_status": None,               # 'registered','collected','in_transit','under_testing','tested'
    "report_status": None,               # 'not_generated','generated','delivered'
    "grievance_id": None,
}



# ── PERSONA STATES ──────────────────────────────
# Each persona is a filled INITIAL_STATE instance.
# Pass one of these to StubContext() at scenario start.

PERSONA_A = {"otp_sent": False, "otp_verified": False, "session_token": None, "sample_id": None, "sample_status": None, "report_status": None, "grievance_id": None}
PERSONA_B = {"otp_sent": True, "otp_verified": True, "session_token": "SHC-TKN-AB12CD34", "sample_id": "SHC-SMP-50000001", "sample_status": "collected", "report_status": "not_generated", "grievance_id": None}
PERSONA_C = {"otp_sent": True, "otp_verified": True, "session_token": "SHC-TKN-EF56GH78", "sample_id": "SHC-SMP-50000002", "sample_status": "tested", "report_status": "generated", "grievance_id": None}
PERSONA_D = {"otp_sent": True, "otp_verified": True, "session_token": "SHC-TKN-IJ90KL12", "sample_id": "SHC-SMP-50000003", "sample_status": "tested", "report_status": "generated", "grievance_id": None}
PERSONA_E = {"otp_sent": True, "otp_verified": True, "session_token": "SHC-TKN-MN34OP56", "sample_id": "SHC-SMP-50000004", "sample_status": "tested", "report_status": "generated", "grievance_id": None}
PERSONA_F = {"otp_sent": True, "otp_verified": True, "session_token": "SHC-TKN-QR78ST90", "sample_id": "SHC-SMP-50000005", "sample_status": "registered", "report_status": "not_generated", "grievance_id": None}
PERSONA_G = {"otp_sent": True, "otp_verified": True, "session_token": "SHC-TKN-UV12WX34", "sample_id": "SHC-SMP-50000006", "sample_status": "tested", "report_status": "generated", "grievance_id": None}
PERSONA_H = {"otp_sent": True, "otp_verified": True, "session_token": "SHC-TKN-YZ56AB78", "sample_id": "SHC-SMP-50000007", "sample_status": "tested", "report_status": "delivered", "grievance_id": None}

ALL_PERSONAS = {
    "PERSONA_A": PERSONA_A,
    "PERSONA_B": PERSONA_B,
    "PERSONA_C": PERSONA_C,
    "PERSONA_D": PERSONA_D,
    "PERSONA_E": PERSONA_E,
    "PERSONA_F": PERSONA_F,
    "PERSONA_G": PERSONA_G,
    "PERSONA_H": PERSONA_H
}

def get_persona(persona_id: str) -> dict:
    """Return a fresh copy of the named persona state."""
    if persona_id not in ALL_PERSONAS:
        raise ValueError(
            f"Unknown persona '{persona_id}'. "
            f"Valid: {list(ALL_PERSONAS.keys())}")
    return ALL_PERSONAS[persona_id].copy()


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
    if not isinstance(v, str) or not re.fullmatch(r"SHC-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match SHC-TKN-XXXXXXXX")

def _gen_token():
    return "SHC-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def _gen_id(prefix):
    return prefix + "".join(random.choices(string.digits, k=8))


def shc_generate_otp(state: dict, **kwargs) -> dict:
    """Sends OTP for SHC authentication.
    Reads: nothing
    Mutates: otp_sent
    """
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    m = kwargs.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m):
        raise ToolValidationError("mobile_number", m, "Must be exactly 10 digits")
    state["otp_sent"] = True
    return {"status": "success", "message": "OTP sent to registered mobile number"}


def shc_verify_otp(state: dict, **kwargs) -> dict:
    """Verifies OTP and returns session_token.
    Reads: otp_sent
    Mutates: otp_verified, session_token
    """
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    _validate_otp(kwargs.get("otp"))
    if not state.get("otp_sent"):
        return {"status": "error", "code": "OTP_NOT_SENT", "message": "OTP not generated. Call shc_generate_otp first."}
    token = _gen_token()
    state["otp_verified"] = True
    state["session_token"] = token
    return {"status": "success", "session_token": token}


def shc_register_soil_sample(state: dict, **kwargs) -> dict:
    """Registers a new soil sample for testing.
    Reads: session_token
    Mutates: sample_id, sample_status
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    sid = _gen_id("SHC-SMP-")
    state["sample_id"] = sid
    state["sample_status"] = "registered"
    state["report_status"] = "not_generated"
    return {"status": "success", "sample_id": sid, "sample_status": "registered"}


def shc_track_sample_status(state: dict, **kwargs) -> dict:
    """Tracks lifecycle status of a soil sample.
    Reads: session_token, sample_status
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    return {
        "status": "success",
        "sample_id": kwargs.get("sample_id"),
        "sample_status": state.get("sample_status", "registered"),
    }


def shc_request_soil_test(state: dict, **kwargs) -> dict:
    """Submits request for lab testing of collected sample.
    Reads: session_token, sample_status
    Mutates: sample_status
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("sample_status") not in ("collected", "in_transit"):
        return {"status": "error", "code": "NOT_COLLECTED", "message": "Sample must be collected first."}
    state["sample_status"] = "under_testing"
    return {"status": "success", "sample_status": "under_testing"}


def shc_generate_soil_health_card(state: dict, **kwargs) -> dict:
    """Generates the Soil Health Card report.
    Reads: session_token, sample_status
    Mutates: report_status
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("sample_status") != "tested":
        return {"status": "error", "code": "NOT_TESTED", "message": "Sample must be tested first."}
    state["report_status"] = "generated"
    return {"status": "success", "report_status": "generated", "sample_id": kwargs.get("sample_id")}


def shc_get_nutrient_analysis(state: dict, **kwargs) -> dict:
    """Retrieves detailed nutrient analysis from SHC report.
    Reads: session_token, report_status
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("report_status") not in ("generated", "delivered"):
        return {"status": "error", "code": "REPORT_NOT_READY", "message": "Report not generated yet."}
    return {
        "status": "success",
        "sample_id": kwargs.get("sample_id"),
        "nutrients": {
            "nitrogen": {"value": 280, "unit": "kg/ha", "status": "medium"},
            "phosphorus": {"value": 22, "unit": "kg/ha", "status": "medium"},
            "potassium": {"value": 310, "unit": "kg/ha", "status": "high"},
            "organic_carbon": {"value": 0.55, "unit": "%", "status": "medium"},
            "ph": {"value": 6.8, "unit": "pH", "status": "normal"},
            "micronutrients": {"zinc": 1.2, "iron": 8.5, "manganese": 5.0, "copper": 1.8},
        },
    }


def shc_get_fertilizer_recommendation(state: dict, **kwargs) -> dict:
    """Generates fertilizer recommendations based on SHC results.
    Reads: session_token, report_status
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("report_status") not in ("generated", "delivered"):
        return {"status": "error", "code": "REPORT_NOT_READY", "message": "Report not generated yet."}
    return {
        "status": "success",
        "crop_type": kwargs.get("crop_type"),
        "recommendations": [
            {"fertilizer": "Urea", "quantity_kg_per_hectare": 120},
            {"fertilizer": "DAP", "quantity_kg_per_hectare": 60},
            {"fertilizer": "MOP", "quantity_kg_per_hectare": 40},
        ],
    }


def shc_get_soil_improvement_advisory(state: dict, **kwargs) -> dict:
    """Provides soil improvement advisory based on SHC results.
    Reads: session_token, report_status
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("report_status") not in ("generated", "delivered"):
        return {"status": "error", "code": "REPORT_NOT_READY", "message": "Report not generated yet."}
    valid_types = ("fertilizer", "soil_improvement", "crop_suitability")
    at = kwargs.get("advisory_type")
    if at not in valid_types:
        raise ToolValidationError("advisory_type", at, f"Must be one of {valid_types}")
    return {
        "status": "success",
        "advisory_type": at,
        "recommendations": ["Add organic manure to improve soil carbon", "Apply gypsum for pH correction"],
    }


def shc_get_crop_suitability(state: dict, **kwargs) -> dict:
    """Returns list of crops suitable for the soil.
    Reads: session_token, report_status
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("report_status") not in ("generated", "delivered"):
        return {"status": "error", "code": "REPORT_NOT_READY", "message": "Report not generated yet."}
    return {
        "status": "success",
        "suitable_crops": ["paddy", "wheat", "maize", "pulses"],
    }


def shc_get_sample_history(state: dict, **kwargs) -> dict:
    """Retrieves all historical soil samples and reports.
    Reads: session_token
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    return {
        "status": "success",
        "samples": [
            {"sample_id": state.get("sample_id", "SHC-SMP-00000001"), "status": state.get("sample_status", "registered"), "report_status": state.get("report_status", "not_generated")},
        ],
    }


def shc_get_lab_status(state: dict, **kwargs) -> dict:
    """Returns assigned soil testing lab details.
    Reads: session_token
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    return {
        "status": "success",
        "lab_name": "District Soil Testing Laboratory",
        "turnaround_days": 15,
        "queue_position": 12,
    }


def shc_raise_grievance(state: dict, **kwargs) -> dict:
    """Raises an SHC grievance.
    Reads: session_token
    Mutates: grievance_id
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    valid_cats = ("sample_not_collected", "report_not_generated", "incorrect_values", "lab_delay", "recommendation_issue")
    cat = kwargs.get("grievance_category")
    if cat not in valid_cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {valid_cats}")
    if not kwargs.get("description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description cannot be empty."}
    gid = _gen_id("SHC-GRV-")
    state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}


def shc_track_grievance_status(state: dict, **kwargs) -> dict:
    """Tracks an SHC grievance.
    Reads: session_token
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    gid = kwargs.get("grievance_id")
    if not gid:
        return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending", "remarks": None}


STUBS = {
    "shc_generate_otp": shc_generate_otp,
    "shc_verify_otp": shc_verify_otp,
    "shc_register_soil_sample": shc_register_soil_sample,
    "shc_track_sample_status": shc_track_sample_status,
    "shc_request_soil_test": shc_request_soil_test,
    "shc_generate_soil_health_card": shc_generate_soil_health_card,
    "shc_get_nutrient_analysis": shc_get_nutrient_analysis,
    "shc_get_fertilizer_recommendation": shc_get_fertilizer_recommendation,
    "shc_get_soil_improvement_advisory": shc_get_soil_improvement_advisory,
    "shc_get_crop_suitability": shc_get_crop_suitability,
    "shc_get_sample_history": shc_get_sample_history,
    "shc_get_lab_status": shc_get_lab_status,
    "shc_raise_grievance": shc_raise_grievance,
    "shc_track_grievance_status": shc_track_grievance_status,
}
