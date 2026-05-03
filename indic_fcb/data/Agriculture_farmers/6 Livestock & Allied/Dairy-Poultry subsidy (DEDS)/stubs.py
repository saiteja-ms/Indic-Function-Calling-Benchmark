import re, random, string

class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field, self.value, self.reason = field, value, reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")

INITIAL_STATE = {
    "otp_sent": False, "otp_verified": False, "session_token": None,
    "eligibility_status": None, "application_id": None, "application_status": None,
    "loan_status": None, "project_status": None, "subsidy_status": None,
    "inspection_status": None, "grievance_id": None,
}


# ── PERSONA STATES ──────────────────────────────
# Each persona is a filled INITIAL_STATE instance.
# Pass one of these to StubContext() at scenario start.

PERSONA_A = {"otp_sent": False, "otp_verified": False, "session_token": None, "eligibility_status": None, "application_id": None, "application_status": None, "loan_status": None, "project_status": None, "subsidy_status": None, "inspection_status": None, "grievance_id": None}
PERSONA_B = {"otp_sent": True, "otp_verified": True, "session_token": "DEDS-TKN-AB12CD34", "eligibility_status": "eligible", "application_id": "DEDS-APP-20000001", "application_status": "submitted", "loan_status": None, "project_status": "not_started", "subsidy_status": None, "inspection_status": None, "grievance_id": None}
PERSONA_C = {"otp_sent": True, "otp_verified": True, "session_token": "DEDS-TKN-EF56GH78", "eligibility_status": "eligible", "application_id": "DEDS-APP-20000002", "application_status": "approved", "loan_status": "sanctioned", "project_status": "not_started", "subsidy_status": None, "inspection_status": "pending", "grievance_id": None}
PERSONA_D = {"otp_sent": True, "otp_verified": True, "session_token": "DEDS-TKN-IJ90KL12", "eligibility_status": "eligible", "application_id": "DEDS-APP-20000003", "application_status": "approved", "loan_status": "disbursed", "project_status": "verified", "subsidy_status": "pending", "inspection_status": "completed", "grievance_id": None}
PERSONA_E = {"otp_sent": True, "otp_verified": True, "session_token": "DEDS-TKN-MN34OP56", "eligibility_status": "eligible", "application_id": "DEDS-APP-20000004", "application_status": "approved", "loan_status": "disbursed", "project_status": "under_review", "subsidy_status": None, "inspection_status": "completed", "grievance_id": None}
PERSONA_F = {"otp_sent": True, "otp_verified": True, "session_token": "DEDS-TKN-QR78ST90", "eligibility_status": "eligible", "application_id": "DEDS-APP-20000005", "application_status": "under_review", "loan_status": "applied", "project_status": "not_started", "subsidy_status": None, "inspection_status": None, "grievance_id": None}
PERSONA_G = {"otp_sent": True, "otp_verified": True, "session_token": "DEDS-TKN-UV12WX34", "eligibility_status": "eligible", "application_id": "DEDS-APP-20000006", "application_status": "submitted", "loan_status": None, "project_status": None, "subsidy_status": None, "inspection_status": None, "grievance_id": None}
PERSONA_H = {"otp_sent": True, "otp_verified": True, "session_token": "DEDS-TKN-YZ56AB78", "eligibility_status": "eligible", "application_id": "DEDS-APP-20000007", "application_status": "approved", "loan_status": "disbursed", "project_status": "verified", "subsidy_status": "disbursed", "inspection_status": "completed", "grievance_id": None}

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
    if not isinstance(v, str) or not re.fullmatch(r"\d{12}", v): raise ToolValidationError("aadhaar_number", v, "Must be 12 digits")
def _val_otp(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{6}", v): raise ToolValidationError("otp", v, "Must be 6 digits")
def _val_session(v):
    if not isinstance(v, str) or not re.fullmatch(r"DEDS-TKN-[A-Za-z0-9]{8}", v): raise ToolValidationError("session_token", v, "Must match DEDS-TKN-XXXXXXXX")
def _gen_token(): return "DEDS-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
def _gen_id(pfx): return pfx + "".join(random.choices(string.digits, k=8))

def deds_generate_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m): raise ToolValidationError("mobile_number", m, "Must be 10 digits")
    state["otp_sent"] = True
    return {"status": "success", "message": "OTP sent"}

def deds_verify_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number")); _val_otp(kw.get("otp"))
    if not state.get("otp_sent"): return {"status": "error", "code": "OTP_NOT_SENT", "message": "Call deds_generate_otp first."}
    token = _gen_token(); state["otp_verified"] = True; state["session_token"] = token
    return {"status": "success", "session_token": token}

def deds_check_eligibility(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    state["eligibility_status"] = "eligible"
    return {"status": "success", "eligibility_status": "eligible", "project_type": kw.get("project_type")}

def deds_submit_project(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    if state.get("eligibility_status") != "eligible": return {"status": "error", "code": "NOT_ELIGIBLE", "message": "Check eligibility first."}
    aid = _gen_id("DEDS-APP-"); state["application_id"] = aid; state["application_status"] = "submitted"
    return {"status": "success", "application_id": aid, "application_status": "submitted"}

def deds_apply_loan(state, **kw):
    _val_session(kw.get("session_token"))
    if not state.get("application_id"): return {"status": "error", "code": "NO_APPLICATION", "message": "Submit project first."}
    lid = _gen_id("DEDS-LOAN-"); state["loan_status"] = "applied"
    return {"status": "success", "loan_id": lid, "loan_status": "applied"}

def deds_track_loan_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "loan_id": kw.get("loan_id"), "loan_status": state.get("loan_status", "not_applied")}

def deds_calculate_subsidy(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "application_id": kw.get("application_id"), "subsidy_pct": 33, "subsidy_amount": 100000}

def deds_track_project_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "application_id": kw.get("application_id"), "project_status": state.get("project_status", "not_started")}

def deds_verify_project(state, **kw):
    _val_session(kw.get("session_token"))
    result = kw.get("inspection_result")
    if result not in ("passed", "failed"): raise ToolValidationError("inspection_result", result, "Must be 'passed' or 'failed'")
    state["project_status"] = "verified" if result == "passed" else "failed"
    return {"status": "success", "application_id": kw.get("application_id"), "project_status": state["project_status"]}

def deds_track_subsidy(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "application_id": kw.get("application_id"), "subsidy_status": state.get("subsidy_status", "not_initiated")}

def deds_get_scheme_details(state, **kw):
    return {"status": "success", "scheme": "DEDS", "eligible_projects": ["dairy_unit", "poultry_farm", "goat_rearing", "pig_farming"], "subsidy_pct_general": 25, "subsidy_pct_sc_st_women": 33}

def deds_get_bank_list(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "banks": [{"bank_id": "BNK-001", "name": "State Bank of India", "state": kw.get("state")}]}

def deds_schedule_inspection(state, **kw):
    _val_session(kw.get("session_token"))
    state["inspection_status"] = "scheduled"
    return {"status": "success", "application_id": kw.get("application_id"), "inspection_status": "scheduled"}

def deds_cancel_application(state, **kw):
    _val_session(kw.get("session_token"))
    if state.get("application_status") not in ("submitted", "under_review"): return {"status": "error", "code": "CANNOT_CANCEL", "message": "Can only cancel submitted/under_review."}
    state["application_status"] = "cancelled"
    return {"status": "success", "application_status": "cancelled"}

def deds_raise_grievance(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("loan_rejected", "application_rejected", "inspection_failure", "subsidy_not_received", "delay_in_processing")
    if kw.get("grievance_category") not in cats: raise ToolValidationError("grievance_category", kw.get("grievance_category"), f"Must be one of {cats}")
    if not kw.get("description"): return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("DEDS-GRV-"); state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}

def deds_track_grievance_status(state, **kw):
    _val_session(kw.get("session_token"))
    gid = kw.get("grievance_id")
    if not gid: return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending"}

STUBS = {
    "deds_generate_otp": deds_generate_otp, "deds_verify_otp": deds_verify_otp,
    "deds_check_eligibility": deds_check_eligibility, "deds_submit_project": deds_submit_project,
    "deds_apply_loan": deds_apply_loan, "deds_track_loan_status": deds_track_loan_status,
    "deds_calculate_subsidy": deds_calculate_subsidy, "deds_track_project_status": deds_track_project_status,
    "deds_verify_project": deds_verify_project, "deds_track_subsidy": deds_track_subsidy,
    "deds_get_scheme_details": deds_get_scheme_details, "deds_get_bank_list": deds_get_bank_list,
    "deds_schedule_inspection": deds_schedule_inspection, "deds_cancel_application": deds_cancel_application,
    "deds_raise_grievance": deds_raise_grievance, "deds_track_grievance_status": deds_track_grievance_status,
}
