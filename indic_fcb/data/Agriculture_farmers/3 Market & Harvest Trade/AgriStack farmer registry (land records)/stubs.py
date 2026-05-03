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
    "profile_status": None,
    "land_record_status": None,
    "consent_status": None,
    "grievance_id": None,
}



# ── PERSONA STATES ──────────────────────────────
# Each persona is a filled INITIAL_STATE instance.
# Pass one of these to StubContext() at scenario start.

PERSONA_A = {"otp_sent": False, "otp_verified": False, "session_token": None, "farmer_id": None, "land_records": None, "grievance_id": None}
PERSONA_B = {"otp_sent": True, "otp_verified": True, "session_token": "AGRISTACK-TKN-AB12CD34", "farmer_id": "AGRI-FID-11000001", "land_records": "pending", "grievance_id": None}
PERSONA_C = {"otp_sent": True, "otp_verified": True, "session_token": "AGRISTACK-TKN-EF56GH78", "farmer_id": "AGRI-FID-11000002", "land_records": "verified", "grievance_id": None}
PERSONA_D = {"otp_sent": True, "otp_verified": True, "session_token": "AGRISTACK-TKN-IJ90KL12", "farmer_id": "AGRI-FID-11000003", "land_records": "verified", "grievance_id": None}
PERSONA_E = {"otp_sent": True, "otp_verified": True, "session_token": "AGRISTACK-TKN-MN34OP56", "farmer_id": "AGRI-FID-11000004", "land_records": "verified", "grievance_id": None}
PERSONA_F = {"otp_sent": True, "otp_verified": True, "session_token": "AGRISTACK-TKN-QR78ST90", "farmer_id": "AGRI-FID-11000005", "land_records": "verified", "grievance_id": None}
PERSONA_G = {"otp_sent": True, "otp_verified": True, "session_token": "AGRISTACK-TKN-UV12WX34", "farmer_id": "AGRI-FID-11000006", "land_records": "pending", "grievance_id": None}
PERSONA_H = {"otp_sent": True, "otp_verified": True, "session_token": "AGRISTACK-TKN-YZ56AB78", "farmer_id": "AGRI-FID-11000007", "land_records": "verified", "grievance_id": None}

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
    if not isinstance(v, str) or not re.fullmatch(r"AGRISTACK-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match AGRISTACK-TKN-XXXXXXXX")

def _gen_token():
    return "AGRISTACK-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def _gen_id(pfx):
    return pfx + "".join(random.choices(string.digits, k=8))


def agristack_generate_otp(state, **kw):
    """Sends OTP for AgriStack authentication."""
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m):
        raise ToolValidationError("mobile_number", m, "Must be 10 digits")
    state["otp_sent"] = True
    return {"status": "success", "message": "OTP sent to registered mobile number"}


def agristack_verify_otp(state, **kw):
    """Verifies OTP and returns session_token."""
    _val_aadhaar(kw.get("aadhaar_number"))
    _val_otp(kw.get("otp"))
    if not state.get("otp_sent"):
        return {"status": "error", "code": "OTP_NOT_SENT", "message": "Call agristack_generate_otp first."}
    token = _gen_token()
    state["otp_verified"] = True
    state["session_token"] = token
    return {"status": "success", "session_token": token}


def agristack_register_farmer(state, **kw):
    """Registers farmer in AgriStack registry."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    if state.get("profile_status") == "registered":
        return {"status": "error", "code": "DUPLICATE", "message": "Already registered."}
    state["profile_status"] = "registered"
    return {"status": "success", "profile_status": "registered"}


def agristack_get_farmer_profile(state, **kw):
    """Retrieves farmer registry profile."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    if not state.get("profile_status"):
        return {"status": "error", "code": "NOT_REGISTERED", "message": "Farmer not registered."}
    return {"status": "success", "profile_status": state["profile_status"], "aadhaar_number": kw["aadhaar_number"]}


def agristack_fetch_land_records(state, **kw):
    """Fetches land records from state databases."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    return {"status": "success", "records": [{"land_parcel_id": "LP-001", "area_hectares": 2.5, "state": kw.get("state"), "ownership": "individual"}]}


def agristack_verify_land_ownership(state, **kw):
    """Verifies farmer land ownership."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    state["land_record_status"] = "verified"
    return {"status": "success", "land_parcel_id": kw.get("land_parcel_id"), "land_record_status": "verified"}


def agristack_check_land_status(state, **kw):
    """Checks land parcel verification status."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "land_parcel_id": kw.get("land_parcel_id"), "land_record_status": state.get("land_record_status", "unverified")}


def agristack_declare_crop(state, **kw):
    """Declares crop for a verified land parcel."""
    _val_session(kw.get("session_token"))
    if state.get("land_record_status") != "verified":
        return {"status": "error", "code": "LAND_NOT_VERIFIED", "message": "Land must be verified first."}
    return {"status": "success", "land_parcel_id": kw.get("land_parcel_id"), "crop_type": kw.get("crop_type")}


def agristack_manage_consent(state, **kw):
    """Manages data sharing consent."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    action = kw.get("action")
    if action not in ("grant", "revoke"):
        raise ToolValidationError("action", action, "Must be 'grant' or 'revoke'")
    state["consent_status"] = "granted" if action == "grant" else "revoked"
    return {"status": "success", "action": action, "service_name": kw.get("service_name"), "consent_status": state["consent_status"]}


def agristack_get_registry_status(state, **kw):
    """Returns comprehensive registry status."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    if not state.get("profile_status"):
        return {"status": "error", "code": "NOT_REGISTERED", "message": "Farmer not registered."}
    return {"status": "success", "profile_status": state["profile_status"], "land_record_status": state.get("land_record_status"), "consent_status": state.get("consent_status")}


def agristack_register_land_parcel(state, **kw):
    """Registers a new land parcel."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    valid_types = ("individual", "joint", "leased")
    ot = kw.get("ownership_type")
    if ot not in valid_types:
        raise ToolValidationError("ownership_type", ot, f"Must be one of {valid_types}")
    return {"status": "success", "land_parcel_id": kw.get("land_parcel_id"), "land_record_status": "unverified"}


def agristack_update_profile(state, **kw):
    """Updates farmer profile details."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    if not state.get("profile_status"):
        return {"status": "error", "code": "NOT_REGISTERED", "message": "Farmer not registered."}
    return {"status": "success", "message": "Profile updated successfully."}


def agristack_get_linked_land_parcels(state, **kw):
    """Returns all linked land parcels."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    return {"status": "success", "parcels": [{"land_parcel_id": "LP-001", "area_hectares": 2.5, "status": state.get("land_record_status", "unverified")}]}


def agristack_raise_grievance(state, **kw):
    """Raises AgriStack grievance."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("land_record_mismatch", "ownership_issue", "profile_not_found", "verification_delay", "consent_issue")
    cat = kw.get("grievance_category")
    if cat not in cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {cats}")
    if not kw.get("description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("AGRISTACK-GRV-")
    state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}


def agristack_track_grievance_status(state, **kw):
    """Tracks AgriStack grievance."""
    _val_session(kw.get("session_token"))
    gid = kw.get("grievance_id")
    if not gid:
        return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending"}


STUBS = {
    "agristack_generate_otp": agristack_generate_otp,
    "agristack_verify_otp": agristack_verify_otp,
    "agristack_register_farmer": agristack_register_farmer,
    "agristack_get_farmer_profile": agristack_get_farmer_profile,
    "agristack_fetch_land_records": agristack_fetch_land_records,
    "agristack_verify_land_ownership": agristack_verify_land_ownership,
    "agristack_check_land_status": agristack_check_land_status,
    "agristack_declare_crop": agristack_declare_crop,
    "agristack_manage_consent": agristack_manage_consent,
    "agristack_get_registry_status": agristack_get_registry_status,
    "agristack_register_land_parcel": agristack_register_land_parcel,
    "agristack_update_profile": agristack_update_profile,
    "agristack_get_linked_land_parcels": agristack_get_linked_land_parcels,
    "agristack_raise_grievance": agristack_raise_grievance,
    "agristack_track_grievance_status": agristack_track_grievance_status,
}
