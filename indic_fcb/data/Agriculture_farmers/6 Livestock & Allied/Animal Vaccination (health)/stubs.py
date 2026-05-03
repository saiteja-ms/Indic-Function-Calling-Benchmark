import re, random, string

class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field, self.value, self.reason = field, value, reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")

INITIAL_STATE = {
    "otp_sent": False, "otp_verified": False, "session_token": None,
    "livestock_id": None, "booking_id": None, "vaccination_status": None,
    "service_status": None, "grievance_id": None,
}


# ── PERSONA STATES ──────────────────────────────
# Each persona is a filled INITIAL_STATE instance.
# Pass one of these to StubContext() at scenario start.

PERSONA_A = {"otp_sent": False, "otp_verified": False, "session_token": None, "livestock_id": None, "booking_id": None, "vaccination_status": None, "service_status": None, "grievance_id": None}
PERSONA_B = {"otp_sent": True, "otp_verified": True, "session_token": "LIVESTOCK-TKN-AB12CD34", "livestock_id": "LVS-10000001", "booking_id": None, "vaccination_status": None, "service_status": None, "grievance_id": None}
PERSONA_C = {"otp_sent": True, "otp_verified": True, "session_token": "LIVESTOCK-TKN-EF56GH78", "livestock_id": "LVS-10000002", "booking_id": "LVSBK-10000001", "vaccination_status": "scheduled", "service_status": "requested", "grievance_id": None}
PERSONA_D = {"otp_sent": True, "otp_verified": True, "session_token": "LIVESTOCK-TKN-IJ90KL12", "livestock_id": "LVS-10000003", "booking_id": "LVSBK-10000002", "vaccination_status": "scheduled", "service_status": "requested", "grievance_id": None}
PERSONA_E = {"otp_sent": True, "otp_verified": True, "session_token": "LIVESTOCK-TKN-MN34OP56", "livestock_id": "LVS-10000004", "booking_id": "LVSBK-10000003", "vaccination_status": "missed", "service_status": "missed", "grievance_id": None}
PERSONA_F = {"otp_sent": True, "otp_verified": True, "session_token": "LIVESTOCK-TKN-QR78ST90", "livestock_id": "LVS-10000005", "booking_id": "LVSBK-10000004", "vaccination_status": "scheduled", "service_status": "delayed", "grievance_id": None}
PERSONA_G = {"otp_sent": True, "otp_verified": True, "session_token": "LIVESTOCK-TKN-UV12WX34", "livestock_id": "LVS-10000006", "booking_id": None, "vaccination_status": None, "service_status": None, "grievance_id": None}
PERSONA_H = {"otp_sent": True, "otp_verified": True, "session_token": "LIVESTOCK-TKN-YZ56AB78", "livestock_id": "LVS-10000007", "booking_id": "LVSBK-10000005", "vaccination_status": "scheduled", "service_status": "requested", "grievance_id": None}

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
        self.state, self.call_log = state.copy(), []
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
    if not isinstance(v, str) or not re.fullmatch(r"LIVESTOCK-TKN-[A-Za-z0-9]{8}", v): raise ToolValidationError("session_token", v, "Must match LIVESTOCK-TKN-XXXXXXXX")
def _gen_token(): return "LIVESTOCK-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
def _gen_id(pfx): return pfx + "".join(random.choices(string.digits, k=8))

def livestock_generate_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m): raise ToolValidationError("mobile_number", m, "Must be 10 digits")
    state["otp_sent"] = True
    return {"status": "success", "message": "OTP sent"}

def livestock_verify_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number")); _val_otp(kw.get("otp"))
    if not state.get("otp_sent"): return {"status": "error", "code": "OTP_NOT_SENT", "message": "Call livestock_generate_otp first."}
    token = _gen_token(); state["otp_verified"] = True; state["session_token"] = token
    return {"status": "success", "session_token": token}

def livestock_register_animal(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    valid_types = ("cattle", "buffalo", "sheep", "goat", "poultry")
    if kw.get("animal_type") not in valid_types: raise ToolValidationError("animal_type", kw.get("animal_type"), f"Must be one of {valid_types}")
    lid = _gen_id("LVS-"); state["livestock_id"] = lid
    return {"status": "success", "livestock_id": lid, "livestock_status": "registered"}

def livestock_get_vaccination_schedule(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "livestock_id": kw.get("livestock_id"), "schedule": [{"vaccine": "FMD Vaccine", "due_date": "2024-08-15", "type": "routine"}]}

def livestock_book_vaccination(state, **kw):
    _val_session(kw.get("session_token"))
    valid_diseases = ("fmd", "brucellosis", "ppr", "rabies", "anthrax")
    if kw.get("disease_type") not in valid_diseases: raise ToolValidationError("disease_type", kw.get("disease_type"), f"Must be one of {valid_diseases}")
    bid = _gen_id("LVSBK-"); state["booking_id"] = bid; state["vaccination_status"] = "scheduled"
    return {"status": "success", "booking_id": bid, "vaccination_status": "scheduled"}

def livestock_track_service(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "booking_id": kw.get("booking_id"), "service_status": state.get("service_status", "requested")}

def livestock_record_vaccination(state, **kw):
    _val_session(kw.get("session_token"))
    if state.get("vaccination_status") != "scheduled": return {"status": "error", "code": "NOT_SCHEDULED", "message": "Vaccination not scheduled."}
    state["vaccination_status"] = "administered"
    return {"status": "success", "booking_id": kw.get("booking_id"), "vaccination_status": "administered"}

def livestock_get_vaccination_history(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "livestock_id": kw.get("livestock_id"), "history": [{"vaccine": "FMD", "date": "2024-02-15"}]}

def livestock_reschedule_vaccination(state, **kw):
    _val_session(kw.get("session_token"))
    if state.get("vaccination_status") not in ("scheduled", "missed"): return {"status": "error", "code": "INVALID_STATE", "message": "Must be scheduled/missed."}
    state["vaccination_status"] = "rescheduled"
    return {"status": "success", "booking_id": kw.get("booking_id"), "new_date": kw.get("new_date"), "vaccination_status": "rescheduled"}

def livestock_track_vaccination_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "booking_id": kw.get("booking_id"), "vaccination_status": state.get("vaccination_status", "not_scheduled")}

def livestock_get_disease_advisory(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "animal_type": kw.get("animal_type"), "disease_type": kw.get("disease_type"), "advisory": "Vaccinate biannually. Isolate infected animals."}

def livestock_check_schedule_validity(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "livestock_id": kw.get("livestock_id"), "valid": True, "reason": "Eligible for vaccination."}

def livestock_get_nearest_veterinary_service(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "services": [{"name": "District Veterinary Hospital", "distance_km": 5}]}

def livestock_cancel_service(state, **kw):
    _val_session(kw.get("session_token"))
    if state.get("vaccination_status") == "administered": return {"status": "error", "code": "ALREADY_DONE", "message": "Cannot cancel administered vaccination."}
    state["vaccination_status"] = None; state["service_status"] = "cancelled"
    return {"status": "success", "booking_id": kw.get("booking_id"), "service_status": "cancelled"}

def livestock_raise_grievance(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("service_delay", "vaccination_not_done", "incorrect_record", "schedule_issue", "field_worker_issue")
    if kw.get("grievance_category") not in cats: raise ToolValidationError("grievance_category", kw.get("grievance_category"), f"Must be one of {cats}")
    if not kw.get("description"): return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("LIVESTOCK-GRV-"); state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}

def livestock_track_grievance_status(state, **kw):
    _val_session(kw.get("session_token"))
    gid = kw.get("grievance_id")
    if not gid: return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending"}

STUBS = {
    "livestock_generate_otp": livestock_generate_otp, "livestock_verify_otp": livestock_verify_otp,
    "livestock_register_animal": livestock_register_animal, "livestock_get_vaccination_schedule": livestock_get_vaccination_schedule,
    "livestock_book_vaccination": livestock_book_vaccination, "livestock_track_service": livestock_track_service,
    "livestock_record_vaccination": livestock_record_vaccination, "livestock_get_vaccination_history": livestock_get_vaccination_history,
    "livestock_reschedule_vaccination": livestock_reschedule_vaccination, "livestock_track_vaccination_status": livestock_track_vaccination_status,
    "livestock_get_disease_advisory": livestock_get_disease_advisory, "livestock_check_schedule_validity": livestock_check_schedule_validity,
    "livestock_get_nearest_veterinary_service": livestock_get_nearest_veterinary_service, "livestock_cancel_service": livestock_cancel_service,
    "livestock_raise_grievance": livestock_raise_grievance, "livestock_track_grievance_status": livestock_track_grievance_status,
}
