import re, random, string

class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field, self.value, self.reason = field, value, reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")

INITIAL_STATE = {
    "otp_sent": False, "otp_verified": False, "session_token": None,
    "eligibility_status": None, "application_id": None, "application_status": None,
    "vendor_status": None, "purchase_status": None, "subsidy_status": None, "grievance_id": None,
}


# ── PERSONA STATES ──────────────────────────────
# Each persona is a filled INITIAL_STATE instance.
# Pass one of these to StubContext() at scenario start.

PERSONA_A = {"otp_sent": False, "otp_verified": False, "session_token": None, "eligibility_status": None, "application_id": None, "application_status": None, "vendor_status": None, "purchase_status": None, "subsidy_status": None, "grievance_id": None}
PERSONA_B = {"otp_sent": True, "otp_verified": True, "session_token": "SMAM-TKN-AB12CD34", "eligibility_status": "eligible", "application_id": "SMAM-APP-30000001", "application_status": "submitted", "vendor_status": None, "purchase_status": None, "subsidy_status": None, "grievance_id": None}
PERSONA_C = {"otp_sent": True, "otp_verified": True, "session_token": "SMAM-TKN-EF56GH78", "eligibility_status": "eligible", "application_id": "SMAM-APP-30000002", "application_status": "approved", "vendor_status": "selected", "purchase_status": "pending", "subsidy_status": None, "grievance_id": None}
PERSONA_D = {"otp_sent": True, "otp_verified": True, "session_token": "SMAM-TKN-IJ90KL12", "eligibility_status": "eligible", "application_id": "SMAM-APP-30000003", "application_status": "approved", "vendor_status": "selected", "purchase_status": "verified", "subsidy_status": "processing", "grievance_id": None}
PERSONA_E = {"otp_sent": True, "otp_verified": True, "session_token": "SMAM-TKN-MN34OP56", "eligibility_status": "eligible", "application_id": "SMAM-APP-30000004", "application_status": "under_review", "vendor_status": None, "purchase_status": None, "subsidy_status": None, "grievance_id": None}
PERSONA_F = {"otp_sent": True, "otp_verified": True, "session_token": "SMAM-TKN-QR78ST90", "eligibility_status": "eligible", "application_id": "SMAM-APP-30000005", "application_status": "approved", "vendor_status": "selected", "purchase_status": "pending", "subsidy_status": None, "grievance_id": None}
PERSONA_G = {"otp_sent": True, "otp_verified": True, "session_token": "SMAM-TKN-UV12WX34", "eligibility_status": "eligible", "application_id": "SMAM-APP-30000006", "application_status": "submitted", "vendor_status": None, "purchase_status": None, "subsidy_status": None, "grievance_id": None}
PERSONA_H = {"otp_sent": True, "otp_verified": True, "session_token": "SMAM-TKN-YZ56AB78", "eligibility_status": "eligible", "application_id": "SMAM-APP-30000007", "application_status": "approved", "vendor_status": "selected", "purchase_status": "verified", "subsidy_status": "delayed", "grievance_id": "SMAM-GRV-80000001"}

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
    if not isinstance(v, str) or not re.fullmatch(r"SMAM-TKN-[A-Za-z0-9]{8}", v): raise ToolValidationError("session_token", v, "SMAM-TKN-XXXXXXXX")
def _gen_token(): return "SMAM-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
def _gen_id(pfx): return pfx + "".join(random.choices(string.digits, k=8))

def smam_generate_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number"))
    state["otp_sent"] = True; return {"status": "success", "message": "OTP sent"}

def smam_verify_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number")); _val_otp(kw.get("otp"))
    if not state.get("otp_sent"): return {"status": "error", "code": "OTP_NOT_SENT"}
    t = _gen_token(); state["otp_verified"] = True; state["session_token"] = t
    return {"status": "success", "session_token": t}

def smam_check_eligibility(state, **kw):
    _val_session(kw.get("session_token")); state["eligibility_status"] = "eligible"
    return {"status": "success", "eligibility_status": "eligible"}

def smam_select_machinery(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "machinery_type": kw.get("machinery_type"), "subsidy_pct": 50}

def smam_select_vendor(state, **kw):
    _val_session(kw.get("session_token")); state["vendor_status"] = "selected"
    return {"status": "success", "vendor_id": kw.get("vendor_id"), "vendor_status": "selected"}

def smam_calculate_subsidy(state, **kw):
    _val_session(kw.get("session_token"))
    cost = kw.get("machinery_cost", 100000)
    return {"status": "success", "subsidy_amount": cost * 0.5, "farmer_share": cost * 0.5}

def smam_submit_application(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    aid = _gen_id("SMAM-APP-"); state["application_id"] = aid; state["application_status"] = "submitted"
    return {"status": "success", "application_id": aid, "application_status": "submitted"}

def smam_track_application_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "application_status": state.get("application_status", "not_applied")}

def smam_verify_purchase(state, **kw):
    _val_session(kw.get("session_token")); state["purchase_status"] = "verified"
    return {"status": "success", "purchase_status": "verified"}

def smam_track_subsidy(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "subsidy_status": state.get("subsidy_status", "not_initiated")}

def smam_get_vendor_list(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "vendors": [{"vendor_id": "VND-001", "name": "Mahindra Dealer"}]}

def smam_get_machinery_details(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "machinery_type": kw.get("machinery_type"), "price_range": "150000-500000"}

def smam_schedule_inspection(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "inspection_status": "scheduled"}

def smam_cancel_application(state, **kw):
    _val_session(kw.get("session_token"))
    if state.get("application_status") not in ("submitted", "under_review"): return {"status": "error", "code": "CANNOT_CANCEL"}
    state["application_status"] = "cancelled"; return {"status": "success", "application_status": "cancelled"}

def smam_raise_grievance(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("application_rejected", "vendor_issue", "inspection_failure", "subsidy_not_received", "delay_in_processing")
    if kw.get("grievance_category") not in cats: raise ToolValidationError("grievance_category", kw.get("grievance_category"), f"One of {cats}")
    gid = _gen_id("SMAM-GRV-"); state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}

def smam_track_grievance_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "grievance_id": kw.get("grievance_id"), "resolution_status": "pending"}

STUBS = {
    "smam_generate_otp": smam_generate_otp, "smam_verify_otp": smam_verify_otp,
    "smam_check_eligibility": smam_check_eligibility, "smam_select_machinery": smam_select_machinery,
    "smam_select_vendor": smam_select_vendor, "smam_calculate_subsidy": smam_calculate_subsidy,
    "smam_submit_application": smam_submit_application, "smam_track_application_status": smam_track_application_status,
    "smam_verify_purchase": smam_verify_purchase, "smam_track_subsidy": smam_track_subsidy,
    "smam_get_vendor_list": smam_get_vendor_list, "smam_get_machinery_details": smam_get_machinery_details,
    "smam_schedule_inspection": smam_schedule_inspection, "smam_cancel_application": smam_cancel_application,
    "smam_raise_grievance": smam_raise_grievance, "smam_track_grievance_status": smam_track_grievance_status,
}
