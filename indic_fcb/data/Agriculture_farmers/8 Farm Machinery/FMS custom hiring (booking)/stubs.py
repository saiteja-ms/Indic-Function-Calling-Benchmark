import re, random, string

class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field, self.value, self.reason = field, value, reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")

INITIAL_STATE = {
    "otp_sent": False, "otp_verified": False, "session_token": None,
    "booking_id": None, "booking_status": None, "service_status": None,
    "payment_status": None, "grievance_id": None,
}


# ── PERSONA STATES ──────────────────────────────
# Each persona is a filled INITIAL_STATE instance.
# Pass one of these to StubContext() at scenario start.

PERSONA_A = {"otp_sent": False, "otp_verified": False, "session_token": None, "booking_id": None, "booking_status": None, "service_status": None, "payment_status": None, "grievance_id": None}
PERSONA_B = {"otp_sent": True, "otp_verified": True, "session_token": "FMS-TKN-AB12CD34", "booking_id": None, "booking_status": None, "service_status": None, "payment_status": None, "grievance_id": None}
PERSONA_C = {"otp_sent": True, "otp_verified": True, "session_token": "FMS-TKN-EF56GH78", "booking_id": "FMS-BK-20000001", "booking_status": "requested", "service_status": "not_started", "payment_status": None, "grievance_id": None}
PERSONA_D = {"otp_sent": True, "otp_verified": True, "session_token": "FMS-TKN-IJ90KL12", "booking_id": "FMS-BK-20000002", "booking_status": "assigned", "service_status": "completed", "payment_status": "pending", "grievance_id": None}
PERSONA_E = {"otp_sent": True, "otp_verified": True, "session_token": "FMS-TKN-MN34OP56", "booking_id": "FMS-BK-20000003", "booking_status": "confirmed", "service_status": "not_started", "payment_status": None, "grievance_id": None}
PERSONA_F = {"otp_sent": True, "otp_verified": True, "session_token": "FMS-TKN-QR78ST90", "booking_id": "FMS-BK-20000004", "booking_status": "requested", "service_status": None, "payment_status": None, "grievance_id": None}
PERSONA_G = {"otp_sent": True, "otp_verified": True, "session_token": "FMS-TKN-UV12WX34", "booking_id": "FMS-BK-20000005", "booking_status": "verified", "service_status": "completed", "payment_status": "completed", "grievance_id": None}
PERSONA_H = {"otp_sent": True, "otp_verified": True, "session_token": "FMS-TKN-YZ56AB78", "booking_id": "FMS-BK-20000006", "booking_status": "cancelled", "service_status": None, "payment_status": None, "grievance_id": "FMS-GRV-80000001"}

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
    if not isinstance(v, str) or not re.fullmatch(r"FMS-TKN-[A-Za-z0-9]{8}", v): raise ToolValidationError("session_token", v, "Must match FMS-TKN-XXXXXXXX")
def _gen_token(): return "FMS-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
def _gen_id(pfx): return pfx + "".join(random.choices(string.digits, k=8))

def fms_generate_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m): raise ToolValidationError("mobile_number", m, "10 digits")
    state["otp_sent"] = True; return {"status": "success", "message": "OTP sent"}

def fms_verify_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number")); _val_otp(kw.get("otp"))
    if not state.get("otp_sent"): return {"status": "error", "code": "OTP_NOT_SENT"}
    t = _gen_token(); state["otp_verified"] = True; state["session_token"] = t
    return {"status": "success", "session_token": t}

def fms_get_service_list(state, **kw):
    return {"status": "success", "services": [{"service_id": "SVC-001", "type": kw.get("service_type", "ploughing"), "rate": 800}]}

def fms_search_providers(state, **kw):
    return {"status": "success", "providers": [{"provider_id": "PRV-001", "rating": 4.5}]}

def fms_check_service_availability(state, **kw):
    return {"status": "success", "provider_status": "available"}

def fms_create_booking(state, **kw):
    _val_session(kw.get("session_token"))
    bid = _gen_id("FMS-BK-"); state["booking_id"] = bid; state["booking_status"] = "requested"
    return {"status": "success", "booking_id": bid, "booking_status": "requested"}

def fms_assign_provider(state, **kw):
    _val_session(kw.get("session_token")); state["booking_status"] = "assigned"
    return {"status": "success", "booking_status": "assigned"}

def fms_track_service(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "service_status": state.get("service_status", "not_started")}

def fms_verify_completion(state, **kw):
    _val_session(kw.get("session_token")); state["booking_status"] = "verified"
    return {"status": "success", "booking_status": "verified"}

def fms_track_payment(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "payment_status": state.get("payment_status", "not_initiated")}

def fms_get_booking_history(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "bookings": []}

def fms_reschedule_service(state, **kw):
    _val_session(kw.get("session_token"))
    if state.get("booking_status") not in ("requested", "confirmed"): return {"status": "error", "code": "CANNOT_RESCHEDULE"}
    return {"status": "success", "new_date": kw.get("new_date")}

def fms_cancel_booking(state, **kw):
    _val_session(kw.get("session_token"))
    if state.get("booking_status") not in ("requested", "confirmed"): return {"status": "error", "code": "CANNOT_CANCEL"}
    state["booking_status"] = "cancelled"; return {"status": "success", "booking_status": "cancelled"}

def fms_estimate_cost(state, **kw):
    return {"status": "success", "estimated_cost": kw.get("land_area_acres", 1) * 800}

def fms_get_service_details(state, **kw):
    return {"status": "success", "service_id": kw.get("service_id"), "rate": 800}

def fms_raise_grievance(state, **kw):
    _val_session(kw.get("session_token"))
    cats = ("service_not_completed", "poor_quality_service", "provider_issue", "payment_issue", "scheduling_conflict")
    if kw.get("grievance_category") not in cats: raise ToolValidationError("grievance_category", kw.get("grievance_category"), f"Must be one of {cats}")
    gid = _gen_id("FMS-GRV-"); state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}

def fms_track_grievance_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "grievance_id": kw.get("grievance_id"), "resolution_status": "pending"}

STUBS = {
    "fms_generate_otp": fms_generate_otp, "fms_verify_otp": fms_verify_otp,
    "fms_get_service_list": fms_get_service_list, "fms_search_providers": fms_search_providers,
    "fms_check_service_availability": fms_check_service_availability, "fms_create_booking": fms_create_booking,
    "fms_assign_provider": fms_assign_provider, "fms_track_service": fms_track_service,
    "fms_verify_completion": fms_verify_completion, "fms_track_payment": fms_track_payment,
    "fms_get_booking_history": fms_get_booking_history, "fms_reschedule_service": fms_reschedule_service,
    "fms_cancel_booking": fms_cancel_booking, "fms_estimate_cost": fms_estimate_cost,
    "fms_get_service_details": fms_get_service_details, "fms_raise_grievance": fms_raise_grievance,
    "fms_track_grievance_status": fms_track_grievance_status,
}
