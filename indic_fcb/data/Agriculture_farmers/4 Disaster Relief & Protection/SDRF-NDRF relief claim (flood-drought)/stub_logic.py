import re, random, string


class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")


INITIAL_STATE = {
    "otp_sent": False,
    "otp_verified": False,
    "session_token": None,
    "disaster_status": None,
    "location_eligible": False,
    "claim_id": None,
    "claim_status": None,
    "survey_status": None,
    "payment_status": None,
    "grievance_id": None,
}


class StubContext:
    def __init__(self, state):
        self.state = state.copy()
        self.call_log = []

    def call(self, tool_name, **kwargs):
        self.call_log.append({"tool": tool_name, "args": kwargs})
        if tool_name not in STUBS:
            raise ValueError(f"Unknown tool: {tool_name}")
        return STUBS[tool_name](self.state, **kwargs)

    def get_call_log(self):
        return self.call_log.copy()

    def reset(self, state):
        self.state = state.copy()
        self.call_log = []


def _val_aadhaar(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{12}", v):
        raise ToolValidationError("aadhaar_number", v, "Must be 12 digits")

def _val_otp(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{6}", v):
        raise ToolValidationError("otp", v, "Must be 6 digits")

def _val_session(v):
    if not isinstance(v, str) or not re.fullmatch(r"SDRFNDRF-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match SDRFNDRF-TKN-XXXXXXXX")

def _gen_token():
    return "SDRFNDRF-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def _gen_id(pfx):
    return pfx + "".join(random.choices(string.digits, k=8))


def sdrfndrf_generate_otp(state, **kw):
    """Sends OTP for SDRF/NDRF authentication."""
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m):
        raise ToolValidationError("mobile_number", m, "Must be 10 digits")
    state["otp_sent"] = True
    return {"status": "success", "message": "OTP sent to registered mobile number"}


def sdrfndrf_verify_otp(state, **kw):
    """Verifies OTP and returns session_token."""
    _val_aadhaar(kw.get("aadhaar_number"))
    _val_otp(kw.get("otp"))
    if not state.get("otp_sent"):
        return {"status": "error", "code": "OTP_NOT_SENT", "message": "Call sdrfndrf_generate_otp first."}
    token = _gen_token()
    state["otp_verified"] = True
    state["session_token"] = token
    return {"status": "success", "session_token": token}


def sdrfndrf_check_disaster_status(state, **kw):
    """Checks official disaster declaration status."""
    _val_session(kw.get("session_token"))
    state["disaster_status"] = "declared"
    return {"status": "success", "location": kw.get("location"), "disaster_status": "declared", "disaster_type": kw.get("disaster_type", "flood")}


def sdrfndrf_check_location_eligibility(state, **kw):
    """Verifies location in affected area."""
    _val_session(kw.get("session_token"))
    if state.get("disaster_status") != "declared":
        return {"status": "error", "code": "NO_DISASTER", "message": "No disaster declared."}
    state["location_eligible"] = True
    return {"status": "success", "location": kw.get("location"), "eligible": True}


def sdrfndrf_report_damage(state, **kw):
    """Reports disaster-related damage."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    valid_types = ("flood", "drought", "cyclone", "landslide", "hailstorm")
    dt = kw.get("disaster_type")
    if dt not in valid_types:
        raise ToolValidationError("disaster_type", dt, f"Must be one of {valid_types}")
    valid_sev = ("low", "moderate", "high", "severe")
    ds = kw.get("damage_severity")
    if ds not in valid_sev:
        raise ToolValidationError("damage_severity", ds, f"Must be one of {valid_sev}")
    cid = _gen_id("SDRF-CLM-")
    state["claim_id"] = cid
    state["claim_status"] = "reported"
    return {"status": "success", "claim_id": cid, "claim_status": "reported"}


def sdrfndrf_submit_claim(state, **kw):
    """Submits formal relief claim."""
    _val_session(kw.get("session_token"))
    if state.get("claim_status") != "reported":
        return {"status": "error", "code": "NOT_REPORTED", "message": "Report damage first."}
    state["claim_status"] = "submitted"
    return {"status": "success", "claim_id": kw.get("claim_id"), "claim_status": "submitted"}


def sdrfndrf_track_claim_status(state, **kw):
    """Tracks claim status."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "claim_id": kw.get("claim_id"), "claim_status": state.get("claim_status", "not_reported")}


def sdrfndrf_track_survey_status(state, **kw):
    """Tracks government survey status."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "claim_id": kw.get("claim_id"), "survey_status": state.get("survey_status", "not_started")}


def sdrfndrf_get_assessment_result(state, **kw):
    """Retrieves damage assessment results."""
    _val_session(kw.get("session_token"))
    if state.get("survey_status") != "completed":
        return {"status": "error", "code": "SURVEY_NOT_DONE", "message": "Survey not completed."}
    return {"status": "success", "claim_id": kw.get("claim_id"), "damage_severity": "high", "estimated_loss": 75000}


def sdrfndrf_track_payment(state, **kw):
    """Tracks relief payment status."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "claim_id": kw.get("claim_id"), "payment_status": state.get("payment_status", "not_initiated")}


def sdrfndrf_upload_evidence(state, **kw):
    """Uploads damage evidence."""
    _val_session(kw.get("session_token"))
    if state.get("claim_status") not in ("reported", "submitted"):
        return {"status": "error", "code": "INVALID_STATE", "message": "Claim must be reported/submitted."}
    return {"status": "success", "claim_id": kw.get("claim_id"), "evidence_type": kw.get("evidence_type"), "uploaded": True}


def sdrfndrf_calculate_relief_amount(state, **kw):
    """Calculates estimated relief amount."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "claim_id": kw.get("claim_id"), "relief_amount": 50000}


def sdrfndrf_check_claim_window(state, **kw):
    """Checks if reporting window is open."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "location": kw.get("location"), "window_open": True, "deadline": "30 days from disaster declaration"}


def sdrfndrf_raise_grievance(state, **kw):
    """Raises SDRF/NDRF grievance."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("claim_rejected", "survey_delay", "incorrect_assessment", "payment_delay", "eligibility_issue")
    cat = kw.get("grievance_category")
    if cat not in cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {cats}")
    if not kw.get("description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("SDRFNDRF-GRV-")
    state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}


def sdrfndrf_track_grievance_status(state, **kw):
    """Tracks SDRF/NDRF grievance."""
    _val_session(kw.get("session_token"))
    gid = kw.get("grievance_id")
    if not gid:
        return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending"}


STUBS = {
    "sdrfndrf_generate_otp": sdrfndrf_generate_otp,
    "sdrfndrf_verify_otp": sdrfndrf_verify_otp,
    "sdrfndrf_check_disaster_status": sdrfndrf_check_disaster_status,
    "sdrfndrf_check_location_eligibility": sdrfndrf_check_location_eligibility,
    "sdrfndrf_report_damage": sdrfndrf_report_damage,
    "sdrfndrf_submit_claim": sdrfndrf_submit_claim,
    "sdrfndrf_track_claim_status": sdrfndrf_track_claim_status,
    "sdrfndrf_track_survey_status": sdrfndrf_track_survey_status,
    "sdrfndrf_get_assessment_result": sdrfndrf_get_assessment_result,
    "sdrfndrf_track_payment": sdrfndrf_track_payment,
    "sdrfndrf_upload_evidence": sdrfndrf_upload_evidence,
    "sdrfndrf_calculate_relief_amount": sdrfndrf_calculate_relief_amount,
    "sdrfndrf_check_claim_window": sdrfndrf_check_claim_window,
    "sdrfndrf_raise_grievance": sdrfndrf_raise_grievance,
    "sdrfndrf_track_grievance_status": sdrfndrf_track_grievance_status,
}
