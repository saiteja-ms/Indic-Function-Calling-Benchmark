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
    "ticket_id": None,
    "grievance_status": None,
    "response_status": None,
    "feedback_status": None,
}


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
    if not isinstance(v, str) or not re.fullmatch(r"KCC-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match KCC-TKN-XXXXXXXX")

def _gen_token():
    return "KCC-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def _gen_id(pfx):
    return pfx + "".join(random.choices(string.digits, k=8))


def kcc_generate_otp(state, **kw):
    """Sends OTP for KCC authentication."""
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m):
        raise ToolValidationError("mobile_number", m, "Must be 10 digits")
    state["otp_sent"] = True
    return {"status": "success", "message": "OTP sent to registered mobile number"}


def kcc_verify_otp(state, **kw):
    """Verifies OTP and returns session_token."""
    _val_aadhaar(kw.get("aadhaar_number"))
    _val_otp(kw.get("otp"))
    if not state.get("otp_sent"):
        return {"status": "error", "code": "OTP_NOT_SENT", "message": "Call kcc_generate_otp first."}
    token = _gen_token()
    state["otp_verified"] = True
    state["session_token"] = token
    return {"status": "success", "session_token": token}


def kcc_raise_grievance(state, **kw):
    """Raises a new grievance ticket."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("pmkisan", "pmfby", "pmkusum", "weather", "market", "soil", "other")
    cat = kw.get("grievance_category")
    if cat not in cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {cats}")
    if not kw.get("description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    tid = _gen_id("KCC-TKT-")
    state["ticket_id"] = tid
    state["grievance_status"] = "raised"
    state["response_status"] = "not_provided"
    return {"status": "success", "ticket_id": tid, "grievance_status": "raised"}


def kcc_get_grievance_status(state, **kw):
    """Returns current grievance status."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "ticket_id": kw.get("ticket_id"), "grievance_status": state.get("grievance_status", "raised")}


def kcc_assign_grievance(state, **kw):
    """Assigns grievance to department."""
    _val_session(kw.get("session_token"))
    if state.get("grievance_status") != "raised":
        return {"status": "error", "code": "INVALID_STATE", "message": "Grievance must be in 'raised' status."}
    state["grievance_status"] = "assigned"
    return {"status": "success", "ticket_id": kw.get("ticket_id"), "grievance_status": "assigned", "department": kw.get("department")}


def kcc_provide_response(state, **kw):
    """Records response for a grievance."""
    _val_session(kw.get("session_token"))
    if state.get("grievance_status") not in ("assigned", "in_progress"):
        return {"status": "error", "code": "INVALID_STATE", "message": "Grievance must be assigned or in_progress."}
    state["response_status"] = "provided"
    state["grievance_status"] = "in_progress"
    return {"status": "success", "ticket_id": kw.get("ticket_id"), "response_status": "provided"}


def kcc_escalate_grievance(state, **kw):
    """Escalates unresolved grievance."""
    _val_session(kw.get("session_token"))
    if state.get("grievance_status") not in ("assigned", "in_progress"):
        return {"status": "error", "code": "INVALID_STATE", "message": "Grievance must be assigned or in_progress."}
    state["grievance_status"] = "escalated"
    return {"status": "success", "ticket_id": kw.get("ticket_id"), "grievance_status": "escalated"}


def kcc_close_grievance(state, **kw):
    """Closes a resolved grievance."""
    _val_session(kw.get("session_token"))
    if state.get("grievance_status") != "resolved":
        return {"status": "error", "code": "NOT_RESOLVED", "message": "Grievance must be resolved first."}
    if not kw.get("closure_confirmation"):
        return {"status": "error", "code": "NO_CONFIRMATION", "message": "Closure confirmation required."}
    state["grievance_status"] = "closed"
    return {"status": "success", "ticket_id": kw.get("ticket_id"), "grievance_status": "closed"}


def kcc_submit_feedback(state, **kw):
    """Submits farmer feedback after resolution."""
    _val_session(kw.get("session_token"))
    if state.get("grievance_status") not in ("resolved", "closed"):
        return {"status": "error", "code": "NOT_RESOLVED", "message": "Grievance must be resolved/closed."}
    rating = kw.get("rating")
    if not isinstance(rating, int) or not 1 <= rating <= 5:
        raise ToolValidationError("rating", rating, "Must be 1-5")
    state["feedback_status"] = "given"
    return {"status": "success", "ticket_id": kw.get("ticket_id"), "feedback_status": "given"}


def kcc_get_grievance_history(state, **kw):
    """Retrieves all past grievances."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    return {"status": "success", "grievances": [{"ticket_id": state.get("ticket_id", "KCC-TKT-00000001"), "status": state.get("grievance_status", "raised")}]}


def kcc_update_grievance_details(state, **kw):
    """Updates grievance description."""
    _val_session(kw.get("session_token"))
    if state.get("grievance_status") not in ("raised", "assigned"):
        return {"status": "error", "code": "INVALID_STATE", "message": "Can only update in raised/assigned status."}
    return {"status": "success", "ticket_id": kw.get("ticket_id"), "message": "Details updated."}


def kcc_resolve_grievance(state, **kw):
    """Marks grievance as resolved."""
    _val_session(kw.get("session_token"))
    if state.get("grievance_status") != "in_progress":
        return {"status": "error", "code": "INVALID_STATE", "message": "Grievance must be in_progress."}
    state["grievance_status"] = "resolved"
    return {"status": "success", "ticket_id": kw.get("ticket_id"), "grievance_status": "resolved"}


def kcc_set_priority(state, **kw):
    """Sets grievance priority level."""
    _val_session(kw.get("session_token"))
    valid = ("low", "medium", "high", "critical")
    pl = kw.get("priority_level")
    if pl not in valid:
        raise ToolValidationError("priority_level", pl, f"Must be one of {valid}")
    return {"status": "success", "ticket_id": kw.get("ticket_id"), "priority_level": pl}


def kcc_track_response_status(state, **kw):
    """Tracks response status for a grievance."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "ticket_id": kw.get("ticket_id"), "response_status": state.get("response_status", "not_provided")}


def kcc_resolve_category_ambiguity(state, **kw):
    """Resolves ambiguous grievance categorization."""
    _val_session(kw.get("session_token"))
    if not kw.get("description"):
        return {"status": "error", "code": "VAGUE_DESCRIPTION", "message": "Description too vague."}
    return {"status": "success", "recommended_category": "pmkisan", "confidence": "high"}


STUBS = {
    "kcc_generate_otp": kcc_generate_otp,
    "kcc_verify_otp": kcc_verify_otp,
    "kcc_raise_grievance": kcc_raise_grievance,
    "kcc_get_grievance_status": kcc_get_grievance_status,
    "kcc_assign_grievance": kcc_assign_grievance,
    "kcc_provide_response": kcc_provide_response,
    "kcc_escalate_grievance": kcc_escalate_grievance,
    "kcc_close_grievance": kcc_close_grievance,
    "kcc_submit_feedback": kcc_submit_feedback,
    "kcc_get_grievance_history": kcc_get_grievance_history,
    "kcc_update_grievance_details": kcc_update_grievance_details,
    "kcc_resolve_grievance": kcc_resolve_grievance,
    "kcc_set_priority": kcc_set_priority,
    "kcc_track_response_status": kcc_track_response_status,
    "kcc_resolve_category_ambiguity": kcc_resolve_category_ambiguity,
}
