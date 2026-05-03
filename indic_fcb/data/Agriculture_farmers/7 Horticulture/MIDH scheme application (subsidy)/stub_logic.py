import re, random, string

class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field, self.value, self.reason = field, value, reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")

INITIAL_STATE = {
    "otp_sent": False, "otp_verified": False, "session_token": None,
    "eligibility_status": None, "application_id": None, "application_status": None,
    "project_status": None, "subsidy_status": None, "inspection_status": None, "grievance_id": None,
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
    if not isinstance(v, str) or not re.fullmatch(r"\d{12}", v): raise ToolValidationError("aadhaar_number", v, "Must be 12 digits")
def _val_otp(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{6}", v): raise ToolValidationError("otp", v, "Must be 6 digits")
def _val_session(v):
    if not isinstance(v, str) or not re.fullmatch(r"MIDH-TKN-[A-Za-z0-9]{8}", v): raise ToolValidationError("session_token", v, "Must match MIDH-TKN-XXXXXXXX")
def _gen_token(): return "MIDH-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
def _gen_id(pfx): return pfx + "".join(random.choices(string.digits, k=8))

def midh_generate_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m): raise ToolValidationError("mobile_number", m, "Must be 10 digits")
    state["otp_sent"] = True; return {"status": "success", "message": "OTP sent"}

def midh_verify_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number")); _val_otp(kw.get("otp"))
    if not state.get("otp_sent"): return {"status": "error", "code": "OTP_NOT_SENT", "message": "Call midh_generate_otp first."}
    token = _gen_token(); state["otp_verified"] = True; state["session_token"] = token
    return {"status": "success", "session_token": token}

def midh_check_eligibility(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    state["eligibility_status"] = "eligible"
    return {"status": "success", "eligibility_status": "eligible"}

def midh_select_component(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "component_type": kw.get("component_type"), "subsidy_pct": 50, "cap_inr": 500000}

def midh_submit_application(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    if state.get("eligibility_status") != "eligible": return {"status": "error", "code": "NOT_ELIGIBLE", "message": "Check eligibility first."}
    aid = _gen_id("MIDH-APP-"); state["application_id"] = aid; state["application_status"] = "submitted"
    return {"status": "success", "application_id": aid, "application_status": "submitted"}

def midh_track_application_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "application_id": kw.get("application_id"), "application_status": state.get("application_status", "not_applied")}

def midh_calculate_subsidy(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "application_id": kw.get("application_id"), "subsidy_pct": 50, "subsidy_amount": 250000}

def midh_track_project_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "application_id": kw.get("application_id"), "project_status": state.get("project_status", "not_started")}

def midh_verify_project(state, **kw):
    _val_session(kw.get("session_token"))
    result = kw.get("inspection_result")
    if result not in ("passed", "failed"): raise ToolValidationError("inspection_result", result, "Must be 'passed' or 'failed'")
    state["project_status"] = "verified" if result == "passed" else "failed"
    return {"status": "success", "project_status": state["project_status"]}

def midh_track_subsidy(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "application_id": kw.get("application_id"), "subsidy_status": state.get("subsidy_status", "not_initiated")}

def midh_get_scheme_details(state, **kw):
    return {"status": "success", "scheme": "MIDH", "components": ["orchard_development", "polyhouse", "greenhouse", "drip_irrigation", "nursery"]}

def midh_schedule_inspection(state, **kw):
    _val_session(kw.get("session_token"))
    state["inspection_status"] = "scheduled"
    return {"status": "success", "application_id": kw.get("application_id"), "inspection_status": "scheduled"}

def midh_cancel_application(state, **kw):
    _val_session(kw.get("session_token"))
    if state.get("application_status") not in ("submitted", "under_review"): return {"status": "error", "code": "CANNOT_CANCEL", "message": "Only submitted/under_review."}
    state["application_status"] = "cancelled"
    return {"status": "success", "application_status": "cancelled"}

def midh_raise_grievance(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("application_rejected", "inspection_failure", "subsidy_not_received", "delay_in_processing", "eligibility_issue")
    if kw.get("grievance_category") not in cats: raise ToolValidationError("grievance_category", kw.get("grievance_category"), f"Must be one of {cats}")
    if not kw.get("description"): return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("MIDH-GRV-"); state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}

def midh_track_grievance_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "grievance_id": kw.get("grievance_id"), "resolution_status": "pending"}

STUBS = {
    "midh_generate_otp": midh_generate_otp, "midh_verify_otp": midh_verify_otp,
    "midh_check_eligibility": midh_check_eligibility, "midh_select_component": midh_select_component,
    "midh_submit_application": midh_submit_application, "midh_track_application_status": midh_track_application_status,
    "midh_calculate_subsidy": midh_calculate_subsidy, "midh_track_project_status": midh_track_project_status,
    "midh_verify_project": midh_verify_project, "midh_track_subsidy": midh_track_subsidy,
    "midh_get_scheme_details": midh_get_scheme_details, "midh_schedule_inspection": midh_schedule_inspection,
    "midh_cancel_application": midh_cancel_application, "midh_raise_grievance": midh_raise_grievance,
    "midh_track_grievance_status": midh_track_grievance_status,
}
