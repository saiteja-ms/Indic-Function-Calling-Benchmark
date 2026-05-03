import re, random, string


class ToolValidationError(Exception):
    def __init__(self, field: str, value, reason: str):
        self.field  = field
        self.value  = value
        self.reason = reason
        super().__init__(
            f"Validation failed for '{field}': "
            f"{reason} (got: {value!r})"
        )


INITIAL_STATE = {
    "otp_sent": False,
    "otp_verified": False,
    "session_token": None,               # PMKUSUM-TKN-XXXXXXXX
    "eligibility_status": None,           # 'eligible', 'not_eligible'
    "application_id": None,               # application identifier
    "application_status": None,           # 'not_applied','submitted','under_review','approved','rejected'
    "vendor_id": None,                    # selected vendor
    "vendor_status": None,                # 'not_selected', 'selected'
    "installation_status": None,          # 'not_started','scheduled','in_progress','completed','verified'
    "subsidy_status": None,               # 'not_initiated','pending','disbursed','failed'
    "grid_connection_status": None,       # 'not_connected','connected','not_applicable'
    "grid_type": None,                    # 'off_grid', 'grid_connected'
    "grievance_id": None,
}


class StubContext:
    def __init__(self, state: dict):
        self.state    = state.copy()
        self.call_log = []

    def call(self, tool_name: str, **kwargs) -> dict:
        self.call_log.append({"tool": tool_name, "args": kwargs})
        if tool_name not in STUBS:
            raise ValueError(f"Unknown tool: {tool_name}")
        return STUBS[tool_name](self.state, **kwargs)

    def get_call_log(self) -> list:
        return self.call_log.copy()

    def reset(self, state: dict):
        self.state    = state.copy()
        self.call_log = []


def _validate_aadhaar(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{12}", v):
        raise ToolValidationError("aadhaar_number", v, "Must be exactly 12 digits")

def _validate_otp(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{6}", v):
        raise ToolValidationError("otp", v, "Must be exactly 6 digits")

def _validate_session(v):
    if not isinstance(v, str) or not re.fullmatch(r"PMKUSUM-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match PMKUSUM-TKN-XXXXXXXX")

def _gen_token():
    return "PMKUSUM-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def _gen_id(prefix):
    return prefix + "".join(random.choices(string.digits, k=8))


def pmkusum_generate_otp(state: dict, **kwargs) -> dict:
    """Sends OTP for PM-KUSUM authentication.
    Reads: nothing
    Mutates: otp_sent
    """
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    if not isinstance(kwargs.get("mobile_number"), str) or not re.fullmatch(r"\d{10}", kwargs["mobile_number"]):
        raise ToolValidationError("mobile_number", kwargs.get("mobile_number"), "Must be exactly 10 digits")
    state["otp_sent"] = True
    return {"status": "success", "message": "OTP sent to registered mobile number"}


def pmkusum_verify_otp(state: dict, **kwargs) -> dict:
    """Verifies OTP and returns session_token.
    Reads: otp_sent
    Mutates: otp_verified, session_token
    """
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    _validate_otp(kwargs.get("otp"))
    if not state.get("otp_sent"):
        return {"status": "error", "code": "OTP_NOT_SENT", "message": "OTP not generated. Call pmkusum_generate_otp first."}
    token = _gen_token()
    state["otp_verified"] = True
    state["session_token"] = token
    return {"status": "success", "session_token": token}


def pmkusum_check_eligibility(state: dict, **kwargs) -> dict:
    """Checks eligibility for PM-KUSUM solar pump subsidy.
    Reads: session_token
    Mutates: eligibility_status
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    state["eligibility_status"] = "eligible"
    return {
        "status": "success",
        "eligibility_status": "eligible",
        "state": kwargs.get("state"),
        "land_area_hectares": kwargs.get("land_area_hectares"),
    }


def pmkusum_apply_subsidy(state: dict, **kwargs) -> dict:
    """Submits solar pump subsidy application.
    Reads: session_token, eligibility_status, application_status
    Mutates: application_id, application_status, grid_type
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    if state.get("eligibility_status") != "eligible":
        return {"status": "error", "code": "NOT_ELIGIBLE", "message": "Farmer not eligible. Check eligibility first."}
    if state.get("application_status") in ("submitted", "under_review", "approved"):
        return {"status": "error", "code": "DUPLICATE_APPLICATION", "message": "Application already exists."}
    valid_pump = ("surface_pump", "submersible_pump")
    if kwargs.get("pump_type") not in valid_pump:
        raise ToolValidationError("pump_type", kwargs.get("pump_type"), f"Must be one of {valid_pump}")
    valid_grid = ("off_grid", "grid_connected")
    if kwargs.get("grid_type") not in valid_grid:
        raise ToolValidationError("grid_type", kwargs.get("grid_type"), f"Must be one of {valid_grid}")
    aid = _gen_id("PMKUSUM-APP-")
    state["application_id"] = aid
    state["application_status"] = "submitted"
    state["vendor_status"] = "not_selected"
    state["installation_status"] = "not_started"
    state["subsidy_status"] = "not_initiated"
    state["grid_type"] = kwargs.get("grid_type")
    return {"status": "success", "application_id": aid, "application_status": "submitted"}


def pmkusum_calculate_subsidy(state: dict, **kwargs) -> dict:
    """Calculates subsidy breakdown.
    Reads: session_token, application_status
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("application_status") == "rejected":
        return {"status": "error", "code": "APPLICATION_REJECTED", "message": "Cannot calculate subsidy for rejected application."}
    return {
        "status": "success",
        "application_id": kwargs.get("application_id"),
        "total_cost": 300000,
        "central_share": 90000,
        "state_share": 90000,
        "farmer_contribution": 120000,
    }


def pmkusum_check_application_status(state: dict, **kwargs) -> dict:
    """Returns current application status.
    Reads: session_token, application_status
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    return {
        "status": "success",
        "application_id": kwargs.get("application_id"),
        "application_status": state.get("application_status", "not_applied"),
    }


def pmkusum_get_vendor_list(state: dict, **kwargs) -> dict:
    """Returns list of empanelled vendors.
    Reads: session_token
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    return {
        "status": "success",
        "vendors": [
            {"vendor_id": "VND-001", "name": "SolarTech India Pvt Ltd", "rating": 4.5},
            {"vendor_id": "VND-002", "name": "GreenPump Solutions", "rating": 4.2},
        ],
    }


def pmkusum_select_vendor(state: dict, **kwargs) -> dict:
    """Selects an empanelled vendor for installation.
    Reads: session_token, application_status
    Mutates: vendor_id, vendor_status
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("application_status") != "approved":
        return {"status": "error", "code": "NOT_APPROVED", "message": "Application must be approved before vendor selection."}
    state["vendor_id"] = kwargs.get("vendor_id")
    state["vendor_status"] = "selected"
    return {"status": "success", "vendor_status": "selected", "vendor_id": kwargs.get("vendor_id")}


def pmkusum_schedule_installation(state: dict, **kwargs) -> dict:
    """Schedules solar pump installation.
    Reads: session_token, vendor_status
    Mutates: installation_status
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("vendor_status") != "selected":
        return {"status": "error", "code": "VENDOR_NOT_SELECTED", "message": "Select a vendor first."}
    state["installation_status"] = "scheduled"
    return {"status": "success", "installation_status": "scheduled", "preferred_date": kwargs.get("preferred_date")}


def pmkusum_track_installation(state: dict, **kwargs) -> dict:
    """Tracks installation progress.
    Reads: session_token, installation_status, vendor_id
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    return {
        "status": "success",
        "application_id": kwargs.get("application_id"),
        "installation_status": state.get("installation_status", "not_started"),
        "vendor_id": state.get("vendor_id"),
    }


def pmkusum_verify_installation(state: dict, **kwargs) -> dict:
    """Records physical verification for installed solar pump.
    Reads: session_token, installation_status
    Mutates: installation_status
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("installation_status") != "completed":
        return {"status": "error", "code": "NOT_COMPLETED", "message": "Installation must be completed before verification."}
    result = kwargs.get("inspection_result")
    if result not in ("passed", "failed"):
        raise ToolValidationError("inspection_result", result, "Must be 'passed' or 'failed'")
    if result == "passed":
        state["installation_status"] = "verified"
    return {
        "status": "success",
        "installation_status": state["installation_status"],
        "inspection_result": result,
        "remarks": kwargs.get("remarks"),
    }


def pmkusum_track_subsidy(state: dict, **kwargs) -> dict:
    """Tracks subsidy disbursement status.
    Reads: session_token, installation_status, subsidy_status
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("installation_status") != "verified":
        return {"status": "error", "code": "NOT_VERIFIED", "message": "Installation must be verified before subsidy tracking."}
    return {
        "status": "success",
        "subsidy_status": state.get("subsidy_status", "not_initiated"),
    }


def pmkusum_get_grid_connection_status(state: dict, **kwargs) -> dict:
    """Checks grid connection status.
    Reads: session_token, grid_type, installation_status
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("grid_type") == "off_grid":
        return {"status": "error", "code": "NOT_APPLICABLE", "message": "Grid connection not applicable for off-grid installations."}
    if state.get("installation_status") not in ("completed", "verified"):
        return {"status": "error", "code": "NOT_COMPLETED", "message": "Installation not completed."}
    return {
        "status": "success",
        "grid_connection_status": state.get("grid_connection_status", "not_connected"),
    }


def pmkusum_raise_grievance(state: dict, **kwargs) -> dict:
    """Raises a PM-KUSUM grievance.
    Reads: session_token
    Mutates: grievance_id
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    valid_cats = ("application_rejected", "installation_delay", "vendor_issue", "subsidy_not_received", "inspection_failure")
    cat = kwargs.get("grievance_category")
    if cat not in valid_cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {valid_cats}")
    if not kwargs.get("description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description cannot be empty."}
    gid = _gen_id("PMKUSUM-GRV-")
    state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}


def pmkusum_track_grievance_status(state: dict, **kwargs) -> dict:
    """Tracks a PM-KUSUM grievance.
    Reads: session_token
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    gid = kwargs.get("grievance_id")
    if not gid:
        return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending", "remarks": None}


STUBS = {
    "pmkusum_generate_otp": pmkusum_generate_otp,
    "pmkusum_verify_otp": pmkusum_verify_otp,
    "pmkusum_check_eligibility": pmkusum_check_eligibility,
    "pmkusum_apply_subsidy": pmkusum_apply_subsidy,
    "pmkusum_calculate_subsidy": pmkusum_calculate_subsidy,
    "pmkusum_check_application_status": pmkusum_check_application_status,
    "pmkusum_get_vendor_list": pmkusum_get_vendor_list,
    "pmkusum_select_vendor": pmkusum_select_vendor,
    "pmkusum_schedule_installation": pmkusum_schedule_installation,
    "pmkusum_track_installation": pmkusum_track_installation,
    "pmkusum_verify_installation": pmkusum_verify_installation,
    "pmkusum_track_subsidy": pmkusum_track_subsidy,
    "pmkusum_get_grid_connection_status": pmkusum_get_grid_connection_status,
    "pmkusum_raise_grievance": pmkusum_raise_grievance,
    "pmkusum_track_grievance_status": pmkusum_track_grievance_status,
}
