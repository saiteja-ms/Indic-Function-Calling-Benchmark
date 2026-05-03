import re, random, string


class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")


INITIAL_STATE = {
    "otp_sent": False, "otp_verified": False, "session_token": None,
    "eligibility_status": None, "transaction_id": None, "transaction_status": None,
    "subsidy_status": None, "grievance_id": None,
}



# ── PERSONA STATES ──────────────────────────────
# Each persona is a filled INITIAL_STATE instance.
# Pass one of these to StubContext() at scenario start.

PERSONA_A = {"otp_sent": True, "otp_verified": True, "session_token": "IFMS-TKN-AB12CD34", "eligibility_status": "eligible", "transaction_id": None, "transaction_status": None, "subsidy_status": None, "grievance_id": None}
PERSONA_B = {"otp_sent": True, "otp_verified": True, "session_token": "IFMS-TKN-EF56GH78", "eligibility_status": "eligible", "transaction_id": "IFMS-TXN-10000001", "transaction_status": "initiated", "subsidy_status": None, "grievance_id": None}
PERSONA_C = {"otp_sent": True, "otp_verified": True, "session_token": "IFMS-TKN-IJ90KL12", "eligibility_status": "eligible", "transaction_id": "IFMS-TXN-10000002", "transaction_status": "completed", "subsidy_status": "not_applied", "grievance_id": None}
PERSONA_D = {"otp_sent": True, "otp_verified": True, "session_token": "IFMS-TKN-MN34OP56", "eligibility_status": "eligible", "transaction_id": None, "transaction_status": None, "subsidy_status": None, "grievance_id": None}
PERSONA_E = {"otp_sent": True, "otp_verified": True, "session_token": "IFMS-TKN-QR78ST90", "eligibility_status": "eligible", "transaction_id": "IFMS-TXN-10000003", "transaction_status": "initiated", "subsidy_status": None, "grievance_id": None}
PERSONA_F = {"otp_sent": True, "otp_verified": True, "session_token": "IFMS-TKN-UV12WX34", "eligibility_status": "eligible", "transaction_id": "IFMS-TXN-10000004", "transaction_status": "completed", "subsidy_status": "applied", "grievance_id": None}
PERSONA_G = {"otp_sent": True, "otp_verified": True, "session_token": "IFMS-TKN-YZ56AB78", "eligibility_status": None, "transaction_id": None, "transaction_status": None, "subsidy_status": None, "grievance_id": None}
PERSONA_H = {"otp_sent": True, "otp_verified": True, "session_token": "IFMS-TKN-WX90YZ12", "eligibility_status": "eligible", "transaction_id": "IFMS-TXN-10000005", "transaction_status": "completed", "subsidy_status": "not_applied", "grievance_id": "IFMS-GRV-80000001"}

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
    if not isinstance(v, str) or not re.fullmatch(r"IFMS-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match IFMS-TKN-XXXXXXXX")
def _gen_token():
    return "IFMS-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
def _gen_id(pfx):
    return pfx + "".join(random.choices(string.digits, k=8))


def ifms_generate_otp(state, **kw):
    """Sends OTP for iFMS authentication."""
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m):
        raise ToolValidationError("mobile_number", m, "Must be 10 digits")
    state["otp_sent"] = True
    return {"status": "success", "message": "OTP sent to registered mobile number"}

def ifms_verify_otp(state, **kw):
    """Verifies OTP and returns session_token."""
    _val_aadhaar(kw.get("aadhaar_number"))
    _val_otp(kw.get("otp"))
    if not state.get("otp_sent"):
        return {"status": "error", "code": "OTP_NOT_SENT", "message": "Call ifms_generate_otp first."}
    token = _gen_token()
    state["otp_verified"] = True
    state["session_token"] = token
    return {"status": "success", "session_token": token}

def ifms_check_eligibility(state, **kw):
    """Checks eligibility for fertilizer subsidy."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    state["eligibility_status"] = "eligible"
    return {"status": "success", "eligibility_status": "eligible", "quantity_limit_kg": 500}

def ifms_get_fertilizer_availability(state, **kw):
    """Checks fertilizer stock at retailers."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "location": kw.get("location"), "inventory": [{"fertilizer_type": kw.get("fertilizer_type", "urea"), "inventory_status": "available"}]}

def ifms_get_retailer_list(state, **kw):
    """Returns authorized retailer list."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "retailers": [{"retailer_id": "RTL-001", "name": "Krishi Kendra", "location": kw.get("location")}]}

def ifms_initiate_purchase(state, **kw):
    """Initiates fertilizer purchase transaction."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    tid = _gen_id("IFMS-TXN-")
    state["transaction_id"] = tid
    state["transaction_status"] = "initiated"
    return {"status": "success", "transaction_id": tid, "transaction_status": "initiated"}

def ifms_validate_transaction(state, **kw):
    """Validates purchase at POS."""
    _val_session(kw.get("session_token"))
    if state.get("transaction_status") != "initiated":
        return {"status": "error", "code": "NOT_INITIATED", "message": "Transaction must be initiated."}
    state["transaction_status"] = "validated"
    return {"status": "success", "transaction_id": kw.get("transaction_id"), "transaction_status": "validated"}

def ifms_complete_purchase(state, **kw):
    """Completes fertilizer purchase."""
    _val_session(kw.get("session_token"))
    if state.get("transaction_status") != "validated":
        return {"status": "error", "code": "NOT_VALIDATED", "message": "Transaction must be validated."}
    state["transaction_status"] = "completed"
    return {"status": "success", "transaction_id": kw.get("transaction_id"), "transaction_status": "completed"}

def ifms_apply_subsidy(state, **kw):
    """Records subsidy against completed purchase."""
    _val_session(kw.get("session_token"))
    if state.get("transaction_status") != "completed":
        return {"status": "error", "code": "NOT_COMPLETED", "message": "Purchase must be completed."}
    state["subsidy_status"] = "applied"
    return {"status": "success", "transaction_id": kw.get("transaction_id"), "subsidy_status": "applied"}

def ifms_track_transaction(state, **kw):
    """Tracks transaction and subsidy status."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "transaction_id": kw.get("transaction_id"), "transaction_status": state.get("transaction_status", "initiated"), "subsidy_status": state.get("subsidy_status", "not_applied")}

def ifms_get_purchase_history(state, **kw):
    """Retrieves past purchase records."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    return {"status": "success", "purchases": [{"transaction_id": "IFMS-TXN-00000001", "fertilizer_type": "urea", "quantity_kg": 50}]}

def ifms_check_inventory_status(state, **kw):
    """Checks inventory at specific retailer."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "retailer_id": kw.get("retailer_id"), "fertilizer_type": kw.get("fertilizer_type"), "inventory_status": "available", "quantity_kg": 500}

def ifms_resolve_transaction_ambiguity(state, **kw):
    """Resolves ambiguous transaction records."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    return {"status": "success", "message": "No ambiguity detected."}

def ifms_cancel_transaction(state, **kw):
    """Cancels initiated transaction."""
    _val_session(kw.get("session_token"))
    if state.get("transaction_status") != "initiated":
        return {"status": "error", "code": "CANNOT_CANCEL", "message": "Can only cancel initiated transactions."}
    state["transaction_status"] = "failed"
    return {"status": "success", "transaction_status": "failed"}

def ifms_calculate_subsidy(state, **kw):
    """Calculates subsidy amount."""
    _val_session(kw.get("session_token"))
    qty = kw.get("quantity_kg", 50)
    return {"status": "success", "fertilizer_type": kw.get("fertilizer_type"), "quantity_kg": qty, "full_price": qty * 30, "subsidized_price": qty * 12, "savings": qty * 18}

def ifms_raise_grievance(state, **kw):
    """Raises iFMS grievance."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("transaction_failed", "subsidy_not_applied", "retailer_issue", "stock_unavailable", "quantity_limit_exceeded")
    cat = kw.get("grievance_category")
    if cat not in cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {cats}")
    if not kw.get("description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("IFMS-GRV-")
    state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}

def ifms_track_grievance_status(state, **kw):
    """Tracks iFMS grievance."""
    _val_session(kw.get("session_token"))
    gid = kw.get("grievance_id")
    if not gid:
        return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending"}


STUBS = {
    "ifms_generate_otp": ifms_generate_otp, "ifms_verify_otp": ifms_verify_otp,
    "ifms_check_eligibility": ifms_check_eligibility, "ifms_get_fertilizer_availability": ifms_get_fertilizer_availability,
    "ifms_get_retailer_list": ifms_get_retailer_list, "ifms_initiate_purchase": ifms_initiate_purchase,
    "ifms_validate_transaction": ifms_validate_transaction, "ifms_complete_purchase": ifms_complete_purchase,
    "ifms_apply_subsidy": ifms_apply_subsidy, "ifms_track_transaction": ifms_track_transaction,
    "ifms_get_purchase_history": ifms_get_purchase_history, "ifms_check_inventory_status": ifms_check_inventory_status,
    "ifms_resolve_transaction_ambiguity": ifms_resolve_transaction_ambiguity, "ifms_cancel_transaction": ifms_cancel_transaction,
    "ifms_calculate_subsidy": ifms_calculate_subsidy, "ifms_raise_grievance": ifms_raise_grievance,
    "ifms_track_grievance_status": ifms_track_grievance_status,
}
