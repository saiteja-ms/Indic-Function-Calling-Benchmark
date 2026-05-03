import re, random, string


class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")


INITIAL_STATE = {
    "otp_sent": False, "otp_verified": False, "session_token": None,
    "usage_status": None, "compliance_status": None, "incentive_status": None,
    "grievance_id": None,
}



# ── PERSONA STATES ──────────────────────────────
# Each persona is a filled INITIAL_STATE instance.
# Pass one of these to StubContext() at scenario start.

PERSONA_A = {"otp_sent": True, "otp_verified": True, "session_token": "PRANAM-TKN-AB12CD34", "usage_status": None, "compliance_status": None, "incentive_status": None, "grievance_id": None}
PERSONA_B = {"otp_sent": True, "otp_verified": True, "session_token": "PRANAM-TKN-EF56GH78", "usage_status": "recorded", "compliance_status": None, "incentive_status": None, "grievance_id": None}
PERSONA_C = {"otp_sent": True, "otp_verified": True, "session_token": "PRANAM-TKN-IJ90KL12", "usage_status": "analyzed", "compliance_status": None, "incentive_status": None, "grievance_id": None}
PERSONA_D = {"otp_sent": True, "otp_verified": True, "session_token": "PRANAM-TKN-MN34OP56", "usage_status": "analyzed", "compliance_status": "compliant", "incentive_status": None, "grievance_id": None}
PERSONA_E = {"otp_sent": True, "otp_verified": True, "session_token": "PRANAM-TKN-QR78ST90", "usage_status": "recorded", "compliance_status": None, "incentive_status": None, "grievance_id": None}
PERSONA_F = {"otp_sent": True, "otp_verified": True, "session_token": "PRANAM-TKN-UV12WX34", "usage_status": "analyzed", "compliance_status": "compliant", "incentive_status": "eligible", "grievance_id": None}
PERSONA_G = {"otp_sent": True, "otp_verified": True, "session_token": "PRANAM-TKN-YZ56AB78", "usage_status": None, "compliance_status": None, "incentive_status": None, "grievance_id": None}
PERSONA_H = {"otp_sent": True, "otp_verified": True, "session_token": "PRANAM-TKN-WX90YZ12", "usage_status": None, "compliance_status": None, "incentive_status": None, "grievance_id": None}

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
    if not isinstance(v, str) or not re.fullmatch(r"PRANAM-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match PRANAM-TKN-XXXXXXXX")
def _gen_token():
    return "PRANAM-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
def _gen_id(pfx):
    return pfx + "".join(random.choices(string.digits, k=8))


def pmpranam_generate_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m):
        raise ToolValidationError("mobile_number", m, "Must be 10 digits")
    state["otp_sent"] = True
    return {"status": "success", "message": "OTP sent to registered mobile number"}

def pmpranam_verify_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number"))
    _val_otp(kw.get("otp"))
    if not state.get("otp_sent"):
        return {"status": "error", "code": "OTP_NOT_SENT", "message": "Call pmpranam_generate_otp first."}
    token = _gen_token()
    state["otp_verified"] = True
    state["session_token"] = token
    return {"status": "success", "session_token": token}

def pmpranam_get_fertilizer_usage(state, **kw):
    """Retrieves fertilizer usage records."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    state["usage_status"] = "recorded"
    return {"status": "success", "season": kw.get("season"), "usage": [{"fertilizer_type": "urea", "quantity_kg": 120}, {"fertilizer_type": "dap", "quantity_kg": 60}]}

def pmpranam_analyze_usage_pattern(state, **kw):
    """Analyzes fertilizer usage patterns."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    if state.get("usage_status") != "recorded":
        return {"status": "error", "code": "NO_USAGE_DATA", "message": "Get usage data first."}
    state["usage_status"] = "analyzed"
    return {"status": "success", "urea_reduction_pct": 15, "balanced_nutrition_score": 72}

def pmpranam_get_recommendation(state, **kw):
    """Provides alternative fertilizer recommendations."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    return {"status": "success", "recommendations": [{"type": "organic", "product": "Vermicompost", "qty_kg": 200}, {"type": "biofertilizer", "product": "Rhizobium", "qty_kg": 5}]}

def pmpranam_check_compliance(state, **kw):
    """Checks compliance with urea reduction targets."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    if state.get("usage_status") != "analyzed":
        return {"status": "error", "code": "NOT_ANALYZED", "message": "Analyze usage first."}
    state["compliance_status"] = "compliant"
    return {"status": "success", "compliance_status": "compliant"}

def pmpranam_check_incentive_eligibility(state, **kw):
    """Checks incentive eligibility."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    state["incentive_status"] = "eligible"
    return {"status": "success", "incentive_status": "eligible"}

def pmpranam_track_incentive_status(state, **kw):
    """Tracks incentive status."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    return {"status": "success", "incentive_status": state.get("incentive_status", "not_eligible")}

def pmpranam_get_alternative_fertilizers(state, **kw):
    """Lists available alternative fertilizers."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "alternatives": [{"name": "Vermicompost", "type": "organic"}, {"name": "Rhizobium", "type": "biofertilizer"}]}

def pmpranam_get_usage_history(state, **kw):
    """Retrieves multi-season usage history."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    return {"status": "success", "history": [{"season": "kharif_2023", "urea_kg": 140}, {"season": "rabi_2023", "urea_kg": 120}]}

def pmpranam_resolve_usage_ambiguity(state, **kw):
    """Resolves conflicting usage data."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    return {"status": "success", "message": "No ambiguity detected."}

def pmpranam_report_usage(state, **kw):
    """Self-reports fertilizer usage."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    state["usage_status"] = "recorded"
    return {"status": "success", "usage_status": "recorded"}

def pmpranam_raise_grievance(state, **kw):
    """Raises PM-PRANAM grievance."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("incorrect_usage_data", "no_incentive_received", "advisory_issue", "data_mismatch", "eligibility_issue")
    cat = kw.get("grievance_category")
    if cat not in cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {cats}")
    if not kw.get("description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("PRANAM-GRV-")
    state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}

def pmpranam_track_grievance_status(state, **kw):
    """Tracks PM-PRANAM grievance."""
    _val_session(kw.get("session_token"))
    gid = kw.get("grievance_id")
    if not gid:
        return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending"}


STUBS = {
    "pmpranam_generate_otp": pmpranam_generate_otp, "pmpranam_verify_otp": pmpranam_verify_otp,
    "pmpranam_get_fertilizer_usage": pmpranam_get_fertilizer_usage, "pmpranam_analyze_usage_pattern": pmpranam_analyze_usage_pattern,
    "pmpranam_get_recommendation": pmpranam_get_recommendation, "pmpranam_check_compliance": pmpranam_check_compliance,
    "pmpranam_check_incentive_eligibility": pmpranam_check_incentive_eligibility, "pmpranam_track_incentive_status": pmpranam_track_incentive_status,
    "pmpranam_get_alternative_fertilizers": pmpranam_get_alternative_fertilizers, "pmpranam_get_usage_history": pmpranam_get_usage_history,
    "pmpranam_resolve_usage_ambiguity": pmpranam_resolve_usage_ambiguity, "pmpranam_report_usage": pmpranam_report_usage,
    "pmpranam_raise_grievance": pmpranam_raise_grievance, "pmpranam_track_grievance_status": pmpranam_track_grievance_status,
}
