import re, random, string

class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field, self.value, self.reason = field, value, reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")

INITIAL_STATE = {
    "otp_sent": False, "otp_verified": False, "session_token": None,
    "eligibility_status": None, "application_id": None, "application_status": None,
    "installation_status": None, "irrigation_status": None, "subsidy_status": None,
    "grievance_id": None,
}


# ── PERSONA STATES ──────────────────────────────
# Each persona is a filled INITIAL_STATE instance.
# Pass one of these to StubContext() at scenario start.

PERSONA_A = {"otp_sent": False, "otp_verified": False, "session_token": None, "eligibility_status": None, "application_id": None, "application_status": None, "installation_status": None, "irrigation_status": None, "subsidy_status": None, "grievance_id": None}
PERSONA_B = {"otp_sent": True, "otp_verified": True, "session_token": "PMKSY-TKN-AB12CD34", "eligibility_status": None, "application_id": None, "application_status": None, "installation_status": None, "irrigation_status": None, "subsidy_status": None, "grievance_id": None}
PERSONA_C = {"otp_sent": True, "otp_verified": True, "session_token": "PMKSY-TKN-EF56GH78", "eligibility_status": "eligible", "application_id": "PMKSY-APP-10000001", "application_status": "submitted", "installation_status": "not_started", "irrigation_status": None, "subsidy_status": None, "grievance_id": None}
PERSONA_D = {"otp_sent": True, "otp_verified": True, "session_token": "PMKSY-TKN-IJ90KL12", "eligibility_status": "eligible", "application_id": "PMKSY-APP-10000002", "application_status": "approved", "installation_status": "in_progress", "irrigation_status": None, "subsidy_status": None, "grievance_id": None}
PERSONA_E = {"otp_sent": True, "otp_verified": True, "session_token": "PMKSY-TKN-MN34OP56", "eligibility_status": "eligible", "application_id": "PMKSY-APP-10000003", "application_status": "approved", "installation_status": "completed", "irrigation_status": "active", "subsidy_status": "cleared", "grievance_id": None}
PERSONA_F = {"otp_sent": True, "otp_verified": True, "session_token": "PMKSY-TKN-QR78ST90", "eligibility_status": "eligible", "application_id": "PMKSY-APP-10000004", "application_status": "approved", "installation_status": "completed", "irrigation_status": "faulty", "subsidy_status": "cleared", "grievance_id": None}
PERSONA_G = {"otp_sent": True, "otp_verified": True, "session_token": "PMKSY-TKN-UV12WX34", "eligibility_status": "eligible", "application_id": "PMKSY-APP-10000005", "application_status": "approved", "installation_status": "completed", "irrigation_status": "active", "subsidy_status": "processing", "grievance_id": None}
PERSONA_H = {"otp_sent": True, "otp_verified": True, "session_token": "PMKSY-TKN-YZ56AB78", "eligibility_status": "eligible", "application_id": "PMKSY-APP-10000006", "application_status": "approved", "installation_status": "completed", "irrigation_status": "active", "subsidy_status": "delayed", "grievance_id": "PMKSY-GRV-80000001"}

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
    def __init__(self, state): self.state, self.call_log = state.copy(), []
    def call(self, tool_name, **kwargs):
        self.call_log.append({"tool": tool_name, "args": kwargs})
        if tool_name not in STUBS: raise ValueError(f"Unknown tool: {tool_name}")
        return STUBS[tool_name](self.state, **kwargs)
    def get_call_log(self): return self.call_log.copy()
    def reset(self, state): self.state, self.call_log = state.copy(), []

def _val_aadhaar(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{12}", v): raise ToolValidationError("aadhaar_number", v, "12 digits")
def _val_otp(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{6}", v): raise ToolValidationError("otp", v, "6 digits")
def _val_session(v):
    if not isinstance(v, str) or not re.fullmatch(r"PMKSY-TKN-[A-Za-z0-9]{8}", v): raise ToolValidationError("session_token", v, "PMKSY-TKN-XXXXXXXX")
def _gen_token(): return "PMKSY-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
def _gen_id(pfx): return pfx + "".join(random.choices(string.digits, k=8))

def pmksy_generate_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m): raise ToolValidationError("mobile_number", m, "10 digits")
    state["otp_sent"] = True; return {"status": "success", "message": "OTP sent"}

def pmksy_verify_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number")); _val_otp(kw.get("otp"))
    if not state.get("otp_sent"): return {"status": "error", "code": "OTP_NOT_SENT"}
    t = _gen_token(); state["otp_verified"] = True; state["session_token"] = t
    return {"status": "success", "session_token": t}

def pmksy_check_eligibility(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    state["eligibility_status"] = "eligible"
    return {"status": "success", "eligibility_status": "eligible"}

def pmksy_select_irrigation_type(state, **kw):
    _val_session(kw.get("session_token"))
    valid = ("drip", "sprinkler", "surface")
    if kw.get("irrigation_type") not in valid: raise ToolValidationError("irrigation_type", kw.get("irrigation_type"), f"Must be one of {valid}")
    return {"status": "success", "irrigation_type": kw.get("irrigation_type"), "subsidy_pct": 55}

def pmksy_submit_application(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    if state.get("eligibility_status") != "eligible": return {"status": "error", "code": "NOT_ELIGIBLE"}
    aid = _gen_id("PMKSY-APP-"); state["application_id"] = aid; state["application_status"] = "submitted"
    return {"status": "success", "application_id": aid, "application_status": "submitted"}

def pmksy_track_application_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "application_status": state.get("application_status", "not_applied")}

def pmksy_track_installation(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "installation_status": state.get("installation_status", "not_started")}

def pmksy_monitor_irrigation(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "irrigation_status": state.get("irrigation_status", "active"), "efficiency_pct": 85}

def pmksy_get_water_availability(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "location": kw.get("location"), "water_availability_status": "available"}

def pmksy_track_subsidy(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "subsidy_status": state.get("subsidy_status", "not_initiated")}

def pmksy_get_scheme_details(state, **kw):
    """PUBLIC."""
    return {"status": "success", "scheme": "PMKSY", "components": ["drip", "sprinkler", "surface"], "subsidy_pct": 55}

def pmksy_get_efficiency_advisory(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "advisory": "Optimize drip schedule to morning hours for 15% water savings."}

def pmksy_schedule_inspection(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "inspection_status": "scheduled"}

def pmksy_update_application(state, **kw):
    _val_session(kw.get("session_token"))
    if state.get("application_status") != "submitted": return {"status": "error", "code": "CANNOT_UPDATE"}
    return {"status": "success", "message": "Application updated."}

def pmksy_raise_grievance(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("application_rejected", "installation_issue", "water_shortage", "subsidy_not_received", "system_failure")
    if kw.get("grievance_category") not in cats: raise ToolValidationError("grievance_category", kw.get("grievance_category"), f"Must be one of {cats}")
    if not kw.get("description"): return {"status": "error", "code": "EMPTY_DESCRIPTION"}
    gid = _gen_id("PMKSY-GRV-"); state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}

def pmksy_track_grievance_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "grievance_id": kw.get("grievance_id"), "resolution_status": "pending"}

STUBS = {
    "pmksy_generate_otp": pmksy_generate_otp, "pmksy_verify_otp": pmksy_verify_otp,
    "pmksy_check_eligibility": pmksy_check_eligibility, "pmksy_select_irrigation_type": pmksy_select_irrigation_type,
    "pmksy_submit_application": pmksy_submit_application, "pmksy_track_application_status": pmksy_track_application_status,
    "pmksy_track_installation": pmksy_track_installation, "pmksy_monitor_irrigation": pmksy_monitor_irrigation,
    "pmksy_get_water_availability": pmksy_get_water_availability, "pmksy_track_subsidy": pmksy_track_subsidy,
    "pmksy_get_scheme_details": pmksy_get_scheme_details, "pmksy_get_efficiency_advisory": pmksy_get_efficiency_advisory,
    "pmksy_schedule_inspection": pmksy_schedule_inspection, "pmksy_update_application": pmksy_update_application,
    "pmksy_raise_grievance": pmksy_raise_grievance, "pmksy_track_grievance_status": pmksy_track_grievance_status,
}
