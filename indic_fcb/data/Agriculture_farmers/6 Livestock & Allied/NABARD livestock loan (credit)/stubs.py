import re, random, string

class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field, self.value, self.reason = field, value, reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")

INITIAL_STATE = {
    "otp_sent": False, "otp_verified": False, "session_token": None,
    "eligibility_status": None, "application_id": None, "application_status": None,
    "loan_id": None, "loan_status": None, "verification_status": None,
    "repayment_status": None, "grievance_id": None,
}


# ── PERSONA STATES ──────────────────────────────
# Each persona is a filled INITIAL_STATE instance.
# Pass one of these to StubContext() at scenario start.

PERSONA_A = {"otp_sent": False, "otp_verified": False, "session_token": None, "eligibility_status": None, "application_id": None, "application_status": None, "loan_id": None, "loan_status": None, "verification_status": None, "repayment_status": None, "grievance_id": None}
PERSONA_B = {"otp_sent": True, "otp_verified": True, "session_token": "NABARD-TKN-AB12CD34", "eligibility_status": "eligible", "application_id": "NABARD-APP-60000001", "application_status": "submitted", "loan_id": None, "loan_status": None, "verification_status": None, "repayment_status": None, "grievance_id": None}
PERSONA_C = {"otp_sent": True, "otp_verified": True, "session_token": "NABARD-TKN-EF56GH78", "eligibility_status": "eligible", "application_id": "NABARD-APP-60000002", "application_status": "approved", "loan_id": "NABARD-LOAN-70000001", "loan_status": "sanctioned", "verification_status": "completed", "repayment_status": None, "grievance_id": None}
PERSONA_D = {"otp_sent": True, "otp_verified": True, "session_token": "NABARD-TKN-IJ90KL12", "eligibility_status": "eligible", "application_id": "NABARD-APP-60000003", "application_status": "approved", "loan_id": "NABARD-LOAN-70000002", "loan_status": "disbursed", "verification_status": "completed", "repayment_status": "active", "grievance_id": None}
PERSONA_E = {"otp_sent": True, "otp_verified": True, "session_token": "NABARD-TKN-MN34OP56", "eligibility_status": "eligible", "application_id": "NABARD-APP-60000004", "application_status": "approved", "loan_id": "NABARD-LOAN-70000003", "loan_status": "defaulted", "verification_status": "completed", "repayment_status": "overdue", "grievance_id": None}
PERSONA_F = {"otp_sent": True, "otp_verified": True, "session_token": "NABARD-TKN-QR78ST90", "eligibility_status": "eligible", "application_id": "NABARD-APP-60000005", "application_status": "approved", "loan_id": "NABARD-LOAN-70000004", "loan_status": "disbursed", "verification_status": "completed", "repayment_status": "completed", "grievance_id": None}
PERSONA_G = {"otp_sent": True, "otp_verified": True, "session_token": "NABARD-TKN-UV12WX34", "eligibility_status": "eligible", "application_id": "NABARD-APP-60000006", "application_status": "approved", "loan_id": "NABARD-LOAN-70000005", "loan_status": "sanctioned", "verification_status": "completed", "repayment_status": None, "grievance_id": None}
PERSONA_H = {"otp_sent": True, "otp_verified": True, "session_token": "NABARD-TKN-YZ56AB78", "eligibility_status": "eligible", "application_id": "NABARD-APP-60000007", "application_status": "rejected", "loan_id": None, "loan_status": None, "verification_status": "completed", "repayment_status": None, "grievance_id": "NABARD-GRV-80000001"}

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
    if not isinstance(v, str) or not re.fullmatch(r"NABARD-TKN-[A-Za-z0-9]{8}", v): raise ToolValidationError("session_token", v, "Must match NABARD-TKN-XXXXXXXX")
def _gen_token(): return "NABARD-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
def _gen_id(pfx): return pfx + "".join(random.choices(string.digits, k=8))

def nabard_generate_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m): raise ToolValidationError("mobile_number", m, "Must be 10 digits")
    state["otp_sent"] = True; return {"status": "success", "message": "OTP sent"}

def nabard_verify_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number")); _val_otp(kw.get("otp"))
    if not state.get("otp_sent"): return {"status": "error", "code": "OTP_NOT_SENT", "message": "Call nabard_generate_otp first."}
    token = _gen_token(); state["otp_verified"] = True; state["session_token"] = token
    return {"status": "success", "session_token": token}

def nabard_check_eligibility(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    state["eligibility_status"] = "eligible"
    return {"status": "success", "eligibility_status": "eligible", "max_loan": 500000}

def nabard_submit_application(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    if state.get("eligibility_status") != "eligible": return {"status": "error", "code": "NOT_ELIGIBLE", "message": "Check eligibility first."}
    aid = _gen_id("NABARD-APP-"); state["application_id"] = aid; state["application_status"] = "submitted"
    return {"status": "success", "application_id": aid, "application_status": "submitted"}

def nabard_verify_documents(state, **kw):
    _val_session(kw.get("session_token"))
    if state.get("application_status") != "submitted": return {"status": "error", "code": "NOT_SUBMITTED", "message": "Submit application first."}
    state["verification_status"] = "in_progress"
    return {"status": "success", "application_id": kw.get("application_id"), "verification_status": "in_progress"}

def nabard_track_application_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "application_id": kw.get("application_id"), "application_status": state.get("application_status", "not_applied")}

def nabard_approve_loan(state, **kw):
    _val_session(kw.get("session_token"))
    lid = _gen_id("NABARD-LOAN-"); state["loan_id"] = lid; state["loan_status"] = "sanctioned"
    return {"status": "success", "loan_id": lid, "loan_status": "sanctioned"}

def nabard_disburse_loan(state, **kw):
    _val_session(kw.get("session_token"))
    if state.get("loan_status") != "sanctioned": return {"status": "error", "code": "NOT_SANCTIONED", "message": "Loan must be sanctioned."}
    state["loan_status"] = "disbursed"
    return {"status": "success", "loan_id": kw.get("loan_id"), "loan_status": "disbursed"}

def nabard_track_repayment(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "loan_id": kw.get("loan_id"), "repayment_status": state.get("repayment_status", "not_started"), "emi_amount": 5000}

def nabard_track_loan_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "loan_id": kw.get("loan_id"), "loan_status": state.get("loan_status", "not_sanctioned")}

def nabard_get_emi_schedule(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "loan_id": kw.get("loan_id"), "schedule": [{"emi_no": 1, "amount": 5000, "due_date": "2024-09-01", "status": "pending"}]}

def nabard_calculate_loan_amount(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "max_eligible": 500000, "indicative_emi": 5000, "tenure_months": 60}

def nabard_handle_default(state, **kw):
    _val_session(kw.get("session_token"))
    state["loan_status"] = "defaulted"
    return {"status": "success", "loan_id": kw.get("loan_id"), "loan_status": "defaulted"}

def nabard_restructure_loan(state, **kw):
    _val_session(kw.get("session_token"))
    if state.get("loan_status") not in ("defaulted", "overdue"): return {"status": "error", "code": "NOT_ELIGIBLE", "message": "Loan must be defaulted/overdue."}
    return {"status": "success", "loan_id": kw.get("loan_id"), "restructure_status": "initiated"}

def nabard_close_loan(state, **kw):
    _val_session(kw.get("session_token"))
    state["loan_status"] = "closed"
    return {"status": "success", "loan_id": kw.get("loan_id"), "loan_status": "closed"}

def nabard_raise_grievance(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("loan_rejected", "disbursement_delay", "repayment_issue", "default_issue", "documentation_issue")
    if kw.get("grievance_category") not in cats: raise ToolValidationError("grievance_category", kw.get("grievance_category"), f"Must be one of {cats}")
    if not kw.get("description"): return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("NABARD-GRV-"); state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}

def nabard_track_grievance_status(state, **kw):
    _val_session(kw.get("session_token"))
    gid = kw.get("grievance_id")
    if not gid: return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending"}

STUBS = {
    "nabard_generate_otp": nabard_generate_otp, "nabard_verify_otp": nabard_verify_otp,
    "nabard_check_eligibility": nabard_check_eligibility, "nabard_submit_application": nabard_submit_application,
    "nabard_verify_documents": nabard_verify_documents, "nabard_track_application_status": nabard_track_application_status,
    "nabard_approve_loan": nabard_approve_loan, "nabard_disburse_loan": nabard_disburse_loan,
    "nabard_track_repayment": nabard_track_repayment, "nabard_track_loan_status": nabard_track_loan_status,
    "nabard_get_emi_schedule": nabard_get_emi_schedule, "nabard_calculate_loan_amount": nabard_calculate_loan_amount,
    "nabard_handle_default": nabard_handle_default, "nabard_restructure_loan": nabard_restructure_loan,
    "nabard_close_loan": nabard_close_loan, "nabard_raise_grievance": nabard_raise_grievance,
    "nabard_track_grievance_status": nabard_track_grievance_status,
}
