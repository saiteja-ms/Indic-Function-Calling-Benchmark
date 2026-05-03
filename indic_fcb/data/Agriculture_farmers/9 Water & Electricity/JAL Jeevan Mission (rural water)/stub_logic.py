import re, random, string

class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field, self.value, self.reason = field, value, reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")

INITIAL_STATE = {
    "otp_sent": False, "otp_verified": False, "session_token": None,
    "application_id": None, "connection_status": None, "complaint_id": None,
    "complaint_status": None, "grievance_id": None,
}

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
    if not isinstance(v, str) or not re.fullmatch(r"JJM-TKN-[A-Za-z0-9]{8}", v): raise ToolValidationError("session_token", v, "JJM-TKN-XXXXXXXX")
def _gen_token(): return "JJM-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
def _gen_id(pfx): return pfx + "".join(random.choices(string.digits, k=8))

def jjm_generate_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m): raise ToolValidationError("mobile_number", m, "10 digits")
    state["otp_sent"] = True; return {"status": "success", "message": "OTP sent"}

def jjm_verify_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number")); _val_otp(kw.get("otp"))
    if not state.get("otp_sent"): return {"status": "error", "code": "OTP_NOT_SENT"}
    t = _gen_token(); state["otp_verified"] = True; state["session_token"] = t
    return {"status": "success", "session_token": t}

def jjm_get_connection_status(state, **kw):
    """PUBLIC."""
    return {"status": "success", "household_id": kw.get("household_id"), "connection_status": state.get("connection_status", "not_applied")}

def jjm_apply_connection(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    aid = _gen_id("JJM-APP-"); state["application_id"] = aid; state["connection_status"] = "applied"
    return {"status": "success", "application_id": aid, "connection_status": "applied"}

def jjm_track_application_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "application_id": kw.get("application_id"), "connection_status": state.get("connection_status", "not_applied")}

def jjm_get_supply_status(state, **kw):
    """PUBLIC."""
    return {"status": "success", "village": kw.get("village"), "supply_status": "available"}

def jjm_get_water_quality(state, **kw):
    """PUBLIC."""
    return {"status": "success", "village": kw.get("village"), "quality_status": "safe", "potability": "yes"}

def jjm_report_issue(state, **kw):
    _val_session(kw.get("session_token"))
    valid_issues = ("no_water_supply", "poor_quality", "leakage", "low_pressure", "irregular_supply")
    it = kw.get("issue_type")
    if it not in valid_issues: raise ToolValidationError("issue_type", it, f"Must be one of {valid_issues}")
    cid = _gen_id("JJM-CMP-"); state["complaint_id"] = cid; state["complaint_status"] = "raised"
    return {"status": "success", "complaint_id": cid, "complaint_status": "raised"}

def jjm_track_complaint(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "complaint_id": kw.get("complaint_id"), "complaint_status": state.get("complaint_status", "raised")}

def jjm_get_infrastructure_status(state, **kw):
    """PUBLIC."""
    return {"status": "success", "village": kw.get("village"), "infrastructure_status": "operational"}

def jjm_get_village_summary(state, **kw):
    """PUBLIC."""
    return {"status": "success", "village": kw.get("village"), "total_households": 250, "connections_installed": 200, "coverage_pct": 80}

def jjm_resolve_household_ambiguity(state, **kw):
    """PUBLIC."""
    return {"status": "success", "matches": [{"household_id": "HH-001", "village": kw.get("village")}]}

def jjm_cancel_application(state, **kw):
    _val_session(kw.get("session_token"))
    if state.get("connection_status") != "applied": return {"status": "error", "code": "CANNOT_CANCEL"}
    state["connection_status"] = "cancelled"
    return {"status": "success", "connection_status": "cancelled"}

def jjm_raise_grievance(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("no_water_supply", "poor_quality", "connection_issue", "delay_in_installation", "infrastructure_problem")
    if kw.get("grievance_category") not in cats: raise ToolValidationError("grievance_category", kw.get("grievance_category"), f"Must be one of {cats}")
    if not kw.get("description"): return {"status": "error", "code": "EMPTY_DESCRIPTION"}
    gid = _gen_id("JJM-GRV-"); state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}

def jjm_track_grievance_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "grievance_id": kw.get("grievance_id"), "resolution_status": "pending"}

STUBS = {
    "jjm_generate_otp": jjm_generate_otp, "jjm_verify_otp": jjm_verify_otp,
    "jjm_get_connection_status": jjm_get_connection_status, "jjm_apply_connection": jjm_apply_connection,
    "jjm_track_application_status": jjm_track_application_status, "jjm_get_supply_status": jjm_get_supply_status,
    "jjm_get_water_quality": jjm_get_water_quality, "jjm_report_issue": jjm_report_issue,
    "jjm_track_complaint": jjm_track_complaint, "jjm_get_infrastructure_status": jjm_get_infrastructure_status,
    "jjm_get_village_summary": jjm_get_village_summary, "jjm_resolve_household_ambiguity": jjm_resolve_household_ambiguity,
    "jjm_cancel_application": jjm_cancel_application, "jjm_raise_grievance": jjm_raise_grievance,
    "jjm_track_grievance_status": jjm_track_grievance_status,
}
