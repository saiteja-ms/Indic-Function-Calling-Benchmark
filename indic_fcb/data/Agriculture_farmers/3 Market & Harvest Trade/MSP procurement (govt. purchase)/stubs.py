import re, random, string


class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")


INITIAL_STATE = {
    "otp_sent": False,
    "otp_verified": False,
    "session_token": None,
    "registration_status": None,
    "procurement_status": None,
    "procurement_token": None,
    "quality_grade": None,
    "payment_status": None,
    "grievance_id": None,
}



# ── PERSONA STATES ──────────────────────────────
# Each persona is a filled INITIAL_STATE instance.
# Pass one of these to StubContext() at scenario start.

PERSONA_A = {"otp_sent": False, "otp_verified": False, "session_token": None, "registration_status": None, "procurement_id": None, "procurement_status": None, "payment_status": None, "grievance_id": None}
PERSONA_B = {"otp_sent": True, "otp_verified": True, "session_token": "MSP-TKN-AB12CD34", "registration_status": "registered", "procurement_id": None, "procurement_status": None, "payment_status": None, "grievance_id": None}
PERSONA_C = {"otp_sent": True, "otp_verified": True, "session_token": "MSP-TKN-EF56GH78", "registration_status": "registered", "procurement_id": "MSP-PROC-90000001", "procurement_status": "scheduled", "payment_status": None, "grievance_id": None}
PERSONA_D = {"otp_sent": True, "otp_verified": True, "session_token": "MSP-TKN-IJ90KL12", "registration_status": "registered", "procurement_id": "MSP-PROC-90000002", "procurement_status": "completed", "payment_status": "pending", "grievance_id": None}
PERSONA_E = {"otp_sent": True, "otp_verified": True, "session_token": "MSP-TKN-MN34OP56", "registration_status": "registered", "procurement_id": "MSP-PROC-90000003", "procurement_status": "completed", "payment_status": "completed", "grievance_id": None}
PERSONA_F = {"otp_sent": True, "otp_verified": True, "session_token": "MSP-TKN-QR78ST90", "registration_status": "registered", "procurement_id": "MSP-PROC-90000004", "procurement_status": "rejected", "payment_status": None, "grievance_id": None}
PERSONA_G = {"otp_sent": True, "otp_verified": True, "session_token": "MSP-TKN-UV12WX34", "registration_status": "registered", "procurement_id": None, "procurement_status": "waiting", "payment_status": None, "grievance_id": None}
PERSONA_H = {"otp_sent": True, "otp_verified": True, "session_token": "MSP-TKN-YZ56AB78", "registration_status": "registered", "procurement_id": "MSP-PROC-90000005", "procurement_status": "completed", "payment_status": "failed", "grievance_id": "MSP-GRV-10000001"}

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
    if not isinstance(v, str) or not re.fullmatch(r"MSP-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match MSP-TKN-XXXXXXXX")

def _gen_token():
    return "MSP-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def _gen_id(pfx):
    return pfx + "".join(random.choices(string.digits, k=8))


def msp_generate_otp(state, **kw):
    """Sends OTP for MSP authentication."""
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m):
        raise ToolValidationError("mobile_number", m, "Must be 10 digits")
    state["otp_sent"] = True
    return {"status": "success", "message": "OTP sent to registered mobile number"}


def msp_verify_otp(state, **kw):
    """Verifies OTP and returns session_token."""
    _val_aadhaar(kw.get("aadhaar_number"))
    _val_otp(kw.get("otp"))
    if not state.get("otp_sent"):
        return {"status": "error", "code": "OTP_NOT_SENT", "message": "Call msp_generate_otp first."}
    token = _gen_token()
    state["otp_verified"] = True
    state["session_token"] = token
    return {"status": "success", "session_token": token}


def msp_register_farmer(state, **kw):
    """Registers farmer for MSP procurement."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    if state.get("registration_status") == "registered":
        return {"status": "error", "code": "DUPLICATE", "message": "Already registered."}
    state["registration_status"] = "registered"
    return {"status": "success", "registration_status": "registered"}


def msp_check_msp_rates(state, **kw):
    """PUBLIC. Returns MSP rates for crops."""
    valid = ("paddy", "wheat", "maize", "bajra", "barley", "pulses", "oilseeds")
    crop = kw.get("crop_type")
    if crop not in valid:
        raise ToolValidationError("crop_type", crop, f"Must be one of {valid}")
    rates = {"paddy": 2183, "wheat": 2275, "maize": 2090, "bajra": 2500, "barley": 1850, "pulses": 6600, "oilseeds": 5650}
    return {"status": "success", "crop_type": crop, "msp_rate_per_quintal": rates[crop]}


def msp_declare_crop(state, **kw):
    """Declares crop for procurement season."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    if state.get("registration_status") != "registered":
        return {"status": "error", "code": "NOT_REGISTERED", "message": "Register first."}
    state["procurement_status"] = "declared"
    return {"status": "success", "procurement_status": "declared", "crop_type": kw.get("crop_type")}


def msp_generate_procurement_token(state, **kw):
    """Generates procurement token for mandi visit."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    if state.get("procurement_status") != "declared":
        return {"status": "error", "code": "NOT_DECLARED", "message": "Declare crop first."}
    tok = _gen_id("MSP-PTOK-")
    state["procurement_token"] = tok
    state["procurement_status"] = "scheduled"
    return {"status": "success", "procurement_token": tok, "procurement_status": "scheduled"}


def msp_get_mandi_list(state, **kw):
    """Returns active procurement mandis."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "mandis": [{"mandi_id": "MSPMND-001", "name": "Central Procurement Centre", "state": kw.get("state")}]}


def msp_schedule_mandi_visit(state, **kw):
    """Schedules mandi visit date."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "procurement_token": kw.get("procurement_token"), "visit_date": kw.get("visit_date")}


def msp_record_produce_delivery(state, **kw):
    """Records produce delivery at mandi."""
    _val_session(kw.get("session_token"))
    if state.get("procurement_status") != "scheduled":
        return {"status": "error", "code": "NOT_SCHEDULED", "message": "Schedule visit first."}
    state["procurement_status"] = "delivered"
    return {"status": "success", "procurement_status": "delivered", "actual_quantity_quintal": kw.get("actual_quantity_quintal")}


def msp_check_quality_status(state, **kw):
    """Checks quality inspection results."""
    _val_session(kw.get("session_token"))
    if state.get("procurement_status") != "delivered":
        return {"status": "error", "code": "NOT_DELIVERED", "message": "Produce not delivered."}
    state["quality_grade"] = "FAQ"
    return {"status": "success", "quality_grade": "FAQ", "quality_status": "accepted"}


def msp_check_procurement_status(state, **kw):
    """Returns current procurement status."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "procurement_token": kw.get("procurement_token"), "procurement_status": state.get("procurement_status", "not_declared")}


def msp_track_payment(state, **kw):
    """Tracks payment status."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "procurement_token": kw.get("procurement_token"), "payment_status": state.get("payment_status", "pending")}


def msp_cancel_token(state, **kw):
    """Cancels procurement token."""
    _val_session(kw.get("session_token"))
    if state.get("procurement_status") in ("delivered", "payment_processed"):
        return {"status": "error", "code": "CANNOT_CANCEL", "message": "Cannot cancel after delivery."}
    state["procurement_status"] = "cancelled"
    return {"status": "success", "procurement_status": "cancelled"}


def msp_raise_grievance(state, **kw):
    """Raises MSP grievance."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("payment_delay", "procurement_rejection", "quantity_mismatch", "mandi_issue", "registration_issue")
    cat = kw.get("grievance_category")
    if cat not in cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {cats}")
    if not kw.get("description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("MSP-GRV-")
    state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}


def msp_track_grievance_status(state, **kw):
    """Tracks MSP grievance."""
    _val_session(kw.get("session_token"))
    gid = kw.get("grievance_id")
    if not gid:
        return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending"}


STUBS = {
    "msp_generate_otp": msp_generate_otp,
    "msp_verify_otp": msp_verify_otp,
    "msp_register_farmer": msp_register_farmer,
    "msp_check_msp_rates": msp_check_msp_rates,
    "msp_declare_crop": msp_declare_crop,
    "msp_generate_procurement_token": msp_generate_procurement_token,
    "msp_get_mandi_list": msp_get_mandi_list,
    "msp_schedule_mandi_visit": msp_schedule_mandi_visit,
    "msp_record_produce_delivery": msp_record_produce_delivery,
    "msp_check_quality_status": msp_check_quality_status,
    "msp_check_procurement_status": msp_check_procurement_status,
    "msp_track_payment": msp_track_payment,
    "msp_cancel_token": msp_cancel_token,
    "msp_raise_grievance": msp_raise_grievance,
    "msp_track_grievance_status": msp_track_grievance_status,
}
