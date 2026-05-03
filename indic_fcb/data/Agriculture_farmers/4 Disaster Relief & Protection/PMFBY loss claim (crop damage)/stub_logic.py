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
    "policy_validated": False,
    "claim_id": None,
    "claim_status": None,
    "survey_status": None,
    "assessment_status": None,
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
    if not isinstance(v, str) or not re.fullmatch(r"PMFBYCLM-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match PMFBYCLM-TKN-XXXXXXXX")

def _gen_token():
    return "PMFBYCLM-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def _gen_id(pfx):
    return pfx + "".join(random.choices(string.digits, k=8))


def pmfbyclaim_generate_otp(state, **kw):
    """Sends OTP for PMFBY claim authentication."""
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m):
        raise ToolValidationError("mobile_number", m, "Must be 10 digits")
    state["otp_sent"] = True
    return {"status": "success", "message": "OTP sent to registered mobile number"}


def pmfbyclaim_verify_otp(state, **kw):
    """Verifies OTP and returns session_token."""
    _val_aadhaar(kw.get("aadhaar_number"))
    _val_otp(kw.get("otp"))
    if not state.get("otp_sent"):
        return {"status": "error", "code": "OTP_NOT_SENT", "message": "Call pmfbyclaim_generate_otp first."}
    token = _gen_token()
    state["otp_verified"] = True
    state["session_token"] = token
    return {"status": "success", "session_token": token}


def pmfbyclaim_validate_policy(state, **kw):
    """Validates active PMFBY policy."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    state["policy_validated"] = True
    return {"status": "success", "policy_id": kw.get("policy_id"), "policy_status": "active", "validated": True}


def pmfbyclaim_check_claim_window(state, **kw):
    """Checks if claim reporting window is open."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "policy_id": kw.get("policy_id"), "window_open": True, "deadline": "72 hours from loss event"}


def pmfbyclaim_report_loss_event(state, **kw):
    """Reports crop loss event."""
    _val_session(kw.get("session_token"))
    valid_loss = ("drought", "flood", "pest_attack", "cyclone", "unseasonal_rainfall")
    lt = kw.get("loss_type")
    if lt not in valid_loss:
        raise ToolValidationError("loss_type", lt, f"Must be one of {valid_loss}")
    cid = _gen_id("PMFBYCLM-")
    state["claim_id"] = cid
    state["claim_status"] = "reported"
    return {"status": "success", "claim_id": cid, "claim_status": "reported"}


def pmfbyclaim_submit_claim(state, **kw):
    """Submits formal claim."""
    _val_session(kw.get("session_token"))
    if state.get("claim_status") != "reported":
        return {"status": "error", "code": "NOT_REPORTED", "message": "Report loss first."}
    state["claim_status"] = "submitted"
    return {"status": "success", "claim_id": kw.get("claim_id"), "claim_status": "submitted"}


def pmfbyclaim_upload_evidence(state, **kw):
    """Uploads evidence for claim."""
    _val_session(kw.get("session_token"))
    if state.get("claim_status") not in ("reported", "submitted"):
        return {"status": "error", "code": "INVALID_STATE", "message": "Claim must be reported/submitted."}
    return {"status": "success", "claim_id": kw.get("claim_id"), "evidence_type": kw.get("evidence_type"), "uploaded": True}


def pmfbyclaim_track_claim_status(state, **kw):
    """Tracks claim lifecycle status."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "claim_id": kw.get("claim_id"), "claim_status": state.get("claim_status", "not_reported")}


def pmfbyclaim_track_survey_status(state, **kw):
    """Tracks field survey status."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "claim_id": kw.get("claim_id"), "survey_status": state.get("survey_status", "not_started")}


def pmfbyclaim_get_assessment_result(state, **kw):
    """Retrieves damage assessment results."""
    _val_session(kw.get("session_token"))
    if state.get("survey_status") != "completed":
        return {"status": "error", "code": "SURVEY_NOT_DONE", "message": "Survey must be completed."}
    return {"status": "success", "claim_id": kw.get("claim_id"), "loss_percentage": 65, "affected_area_hectares": 1.5}


def pmfbyclaim_calculate_compensation(state, **kw):
    """Calculates compensation amount."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "claim_id": kw.get("claim_id"), "compensation_amount": 45000, "calculation_basis": "65% loss on 1.5 hectares"}


def pmfbyclaim_track_payment(state, **kw):
    """Tracks compensation payment status."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "claim_id": kw.get("claim_id"), "payment_status": state.get("payment_status", "not_initiated")}


def pmfbyclaim_raise_grievance(state, **kw):
    """Raises PMFBY claim grievance."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("claim_rejected", "survey_delay", "incorrect_assessment", "payment_delay", "duplicate_claim_issue")
    cat = kw.get("grievance_category")
    if cat not in cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {cats}")
    if not kw.get("description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("PMFBYCLM-GRV-")
    state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}


def pmfbyclaim_track_grievance_status(state, **kw):
    """Tracks grievance status."""
    _val_session(kw.get("session_token"))
    gid = kw.get("grievance_id")
    if not gid:
        return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending"}


STUBS = {
    "pmfbyclaim_generate_otp": pmfbyclaim_generate_otp,
    "pmfbyclaim_verify_otp": pmfbyclaim_verify_otp,
    "pmfbyclaim_validate_policy": pmfbyclaim_validate_policy,
    "pmfbyclaim_check_claim_window": pmfbyclaim_check_claim_window,
    "pmfbyclaim_report_loss_event": pmfbyclaim_report_loss_event,
    "pmfbyclaim_submit_claim": pmfbyclaim_submit_claim,
    "pmfbyclaim_upload_evidence": pmfbyclaim_upload_evidence,
    "pmfbyclaim_track_claim_status": pmfbyclaim_track_claim_status,
    "pmfbyclaim_track_survey_status": pmfbyclaim_track_survey_status,
    "pmfbyclaim_get_assessment_result": pmfbyclaim_get_assessment_result,
    "pmfbyclaim_calculate_compensation": pmfbyclaim_calculate_compensation,
    "pmfbyclaim_track_payment": pmfbyclaim_track_payment,
    "pmfbyclaim_raise_grievance": pmfbyclaim_raise_grievance,
    "pmfbyclaim_track_grievance_status": pmfbyclaim_track_grievance_status,
}
