import re, random, string

class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field, self.value, self.reason = field, value, reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")

INITIAL_STATE = {
    "otp_sent": False, "otp_verified": False, "session_token": None,
    "booking_id": None, "booking_status": None, "payment_status": None, "grievance_id": None,
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
    if not isinstance(v, str) or not re.fullmatch(r"CHC-TKN-[A-Za-z0-9]{8}", v): raise ToolValidationError("session_token", v, "Must match CHC-TKN-XXXXXXXX")
def _gen_token(): return "CHC-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
def _gen_id(pfx): return pfx + "".join(random.choices(string.digits, k=8))

def chc_generate_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m): raise ToolValidationError("mobile_number", m, "Must be 10 digits")
    state["otp_sent"] = True; return {"status": "success", "message": "OTP sent"}

def chc_verify_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number")); _val_otp(kw.get("otp"))
    if not state.get("otp_sent"): return {"status": "error", "code": "OTP_NOT_SENT", "message": "Call chc_generate_otp first."}
    token = _gen_token(); state["otp_verified"] = True; state["session_token"] = token
    return {"status": "success", "session_token": token}

def chc_get_chc_list(state, **kw):
    """PUBLIC. Returns CHC list."""
    if not kw.get("location"): return {"status": "error", "code": "MISSING_LOCATION", "message": "Location required."}
    return {"status": "success", "chc_centres": [{"chc_id": "CHC-001", "name": "Block CHC", "location": kw["location"]}]}

def chc_search_machinery(state, **kw):
    """PUBLIC. Searches available machinery."""
    return {"status": "success", "machinery": [{"machinery_id": "MACH-001", "type": kw.get("machinery_type"), "availability": "available"}]}

def chc_check_availability(state, **kw):
    """PUBLIC. Checks machinery availability for a date."""
    return {"status": "success", "machinery_id": kw.get("machinery_id"), "date": kw.get("date"), "availability_status": "available", "machinery_status": "operational"}

def chc_create_booking(state, **kw):
    _val_session(kw.get("session_token"))
    bid = _gen_id("CHC-BK-"); state["booking_id"] = bid; state["booking_status"] = "requested"
    return {"status": "success", "booking_id": bid, "booking_status": "requested"}

def chc_track_booking(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "booking_id": kw.get("booking_id"), "booking_status": state.get("booking_status", "requested")}

def chc_modify_booking(state, **kw):
    _val_session(kw.get("session_token"))
    if state.get("booking_status") not in ("requested", "confirmed"): return {"status": "error", "code": "CANNOT_MODIFY", "message": "Only requested/confirmed bookings."}
    return {"status": "success", "booking_id": kw.get("booking_id"), "message": "Booking modified."}

def chc_cancel_booking(state, **kw):
    _val_session(kw.get("session_token"))
    if state.get("booking_status") not in ("requested", "confirmed"): return {"status": "error", "code": "CANNOT_CANCEL", "message": "Only requested/confirmed."}
    state["booking_status"] = "cancelled"
    return {"status": "success", "booking_status": "cancelled"}

def chc_track_payment(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "booking_id": kw.get("booking_id"), "payment_status": state.get("payment_status", "not_initiated")}

def chc_get_booking_history(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    return {"status": "success", "bookings": [{"booking_id": "CHC-BK-00000001", "status": "completed"}]}

def chc_resolve_booking_conflict(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "alternatives": [{"date": "2024-09-16", "slot": "morning"}]}

def chc_get_nearest_chc(state, **kw):
    """PUBLIC."""
    return {"status": "success", "chc_centres": [{"chc_id": "CHC-001", "distance_km": 5}]}

def chc_get_machinery_details(state, **kw):
    """PUBLIC."""
    return {"status": "success", "machinery_id": kw.get("machinery_id"), "type": "tractor", "hourly_rate": 500, "condition": "good"}

def chc_validate_time_slot(state, **kw):
    """PUBLIC."""
    return {"status": "success", "valid": True, "conflicts": []}

def chc_raise_grievance(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("booking_failure", "machinery_unavailable", "payment_issue", "scheduling_conflict", "service_issue")
    if kw.get("grievance_category") not in cats: raise ToolValidationError("grievance_category", kw.get("grievance_category"), f"Must be one of {cats}")
    if not kw.get("description"): return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("CHC-GRV-"); state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}

def chc_track_grievance_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "grievance_id": kw.get("grievance_id"), "resolution_status": "pending"}

STUBS = {
    "chc_generate_otp": chc_generate_otp, "chc_verify_otp": chc_verify_otp,
    "chc_get_chc_list": chc_get_chc_list, "chc_search_machinery": chc_search_machinery,
    "chc_check_availability": chc_check_availability, "chc_create_booking": chc_create_booking,
    "chc_track_booking": chc_track_booking, "chc_modify_booking": chc_modify_booking,
    "chc_cancel_booking": chc_cancel_booking, "chc_track_payment": chc_track_payment,
    "chc_get_booking_history": chc_get_booking_history, "chc_resolve_booking_conflict": chc_resolve_booking_conflict,
    "chc_get_nearest_chc": chc_get_nearest_chc, "chc_get_machinery_details": chc_get_machinery_details,
    "chc_validate_time_slot": chc_validate_time_slot, "chc_raise_grievance": chc_raise_grievance,
    "chc_track_grievance_status": chc_track_grievance_status,
}
