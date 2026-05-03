import re, random, string

class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field, self.value, self.reason = field, value, reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")

INITIAL_STATE = {
    "otp_sent": False, "otp_verified": False, "session_token": None,
    "eligibility_status": None, "application_id": None, "application_status": None,
    "booking_id": None, "booking_status": None, "project_status": None, "grievance_id": None,
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
    if not isinstance(v, str) or not re.fullmatch(r"COLDSTOR-TKN-[A-Za-z0-9]{8}", v): raise ToolValidationError("session_token", v, "Must match COLDSTOR-TKN-XXXXXXXX")
def _gen_token(): return "COLDSTOR-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
def _gen_id(pfx): return pfx + "".join(random.choices(string.digits, k=8))

def coldstorage_generate_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m): raise ToolValidationError("mobile_number", m, "Must be 10 digits")
    state["otp_sent"] = True; return {"status": "success", "message": "OTP sent"}

def coldstorage_verify_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number")); _val_otp(kw.get("otp"))
    if not state.get("otp_sent"): return {"status": "error", "code": "OTP_NOT_SENT", "message": "Call coldstorage_generate_otp first."}
    token = _gen_token(); state["otp_verified"] = True; state["session_token"] = token
    return {"status": "success", "session_token": token}

def coldstorage_check_eligibility(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    state["eligibility_status"] = "eligible"
    return {"status": "success", "eligibility_status": "eligible"}

def coldstorage_submit_application(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    aid = _gen_id("COLDSTOR-APP-"); state["application_id"] = aid; state["application_status"] = "submitted"
    return {"status": "success", "application_id": aid, "application_status": "submitted"}

def coldstorage_track_application_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "application_id": kw.get("application_id"), "application_status": state.get("application_status", "not_applied")}

def coldstorage_get_facility_list(state, **kw):
    return {"status": "success", "facilities": [{"facility_id": "FAC-001", "type": "cold_storage", "location": kw.get("location"), "operational_status": "operational"}]}

def coldstorage_check_capacity(state, **kw):
    return {"status": "success", "facility_id": kw.get("facility_id"), "capacity_status": "available", "available_mt": 50}

def coldstorage_book_storage(state, **kw):
    _val_session(kw.get("session_token"))
    bid = _gen_id("COLDSTOR-BK-"); state["booking_id"] = bid; state["booking_status"] = "requested"
    return {"status": "success", "booking_id": bid, "booking_status": "requested"}

def coldstorage_track_booking(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "booking_id": kw.get("booking_id"), "booking_status": state.get("booking_status", "requested")}

def coldstorage_release_storage(state, **kw):
    _val_session(kw.get("session_token"))
    state["booking_status"] = "completed"
    return {"status": "success", "booking_id": kw.get("booking_id"), "booking_status": "completed"}

def coldstorage_get_project_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "application_id": kw.get("application_id"), "project_status": state.get("project_status", "not_started")}

def coldstorage_cancel_booking(state, **kw):
    _val_session(kw.get("session_token"))
    if state.get("booking_status") not in ("requested", "confirmed"): return {"status": "error", "code": "CANNOT_CANCEL", "message": "Only requested/confirmed can be cancelled."}
    state["booking_status"] = "cancelled"
    return {"status": "success", "booking_status": "cancelled"}

def coldstorage_get_nearest_facility(state, **kw):
    return {"status": "success", "facilities": [{"facility_id": "FAC-001", "distance_km": 8}]}

def coldstorage_raise_grievance(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("application_rejected", "facility_unavailable", "booking_issue", "storage_damage", "delay_in_approval")
    if kw.get("grievance_category") not in cats: raise ToolValidationError("grievance_category", kw.get("grievance_category"), f"Must be one of {cats}")
    if not kw.get("description"): return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("COLDSTOR-GRV-"); state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}

def coldstorage_track_grievance_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "grievance_id": kw.get("grievance_id"), "resolution_status": "pending"}

STUBS = {
    "coldstorage_generate_otp": coldstorage_generate_otp, "coldstorage_verify_otp": coldstorage_verify_otp,
    "coldstorage_check_eligibility": coldstorage_check_eligibility, "coldstorage_submit_application": coldstorage_submit_application,
    "coldstorage_track_application_status": coldstorage_track_application_status, "coldstorage_get_facility_list": coldstorage_get_facility_list,
    "coldstorage_check_capacity": coldstorage_check_capacity, "coldstorage_book_storage": coldstorage_book_storage,
    "coldstorage_track_booking": coldstorage_track_booking, "coldstorage_release_storage": coldstorage_release_storage,
    "coldstorage_get_project_status": coldstorage_get_project_status, "coldstorage_cancel_booking": coldstorage_cancel_booking,
    "coldstorage_get_nearest_facility": coldstorage_get_nearest_facility, "coldstorage_raise_grievance": coldstorage_raise_grievance,
    "coldstorage_track_grievance_status": coldstorage_track_grievance_status,
}
