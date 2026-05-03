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
    "report_status": None,
    "grievance_id": None,
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
    if not isinstance(v, str) or not re.fullmatch(r"SHCPORTAL-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match SHCPORTAL-TKN-XXXXXXXX")

def _gen_token():
    return "SHCPORTAL-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def _gen_id(pfx):
    return pfx + "".join(random.choices(string.digits, k=8))


def shcportal_generate_otp(state, **kw):
    """Sends OTP for SHC Portal authentication."""
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m):
        raise ToolValidationError("mobile_number", m, "Must be 10 digits")
    state["otp_sent"] = True
    return {"status": "success", "message": "OTP sent to registered mobile number"}


def shcportal_verify_otp(state, **kw):
    """Verifies OTP and returns session_token."""
    _val_aadhaar(kw.get("aadhaar_number"))
    _val_otp(kw.get("otp"))
    if not state.get("otp_sent"):
        return {"status": "error", "code": "OTP_NOT_SENT", "message": "Call shcportal_generate_otp first."}
    token = _gen_token()
    state["otp_verified"] = True
    state["session_token"] = token
    return {"status": "success", "session_token": token}


def shcportal_search_reports(state, **kw):
    """Searches available SHC reports for a farmer."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    return {"status": "success", "reports": [{"report_id": "SHCR-00000001", "land_parcel_id": "LP-001", "date": "2024-01-15", "report_status": "available"}]}


def shcportal_get_report_details(state, **kw):
    """Retrieves full report details."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "report_id": kw.get("report_id"), "nutrients": {"nitrogen": 280, "phosphorus": 22, "potassium": 310, "ph": 6.8}, "recommendations": ["Apply Urea 120 kg/ha"]}


def shcportal_check_sample_status(state, **kw):
    """Checks soil sample processing status."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "sample_id": kw.get("sample_id"), "sample_status": "report_ready"}


def shcportal_download_report(state, **kw):
    """Initiates download of SHC report."""
    _val_session(kw.get("session_token"))
    state["report_status"] = "downloaded"
    return {"status": "success", "report_id": kw.get("report_id"), "report_status": "downloaded", "download_url": "https://shcportal.gov.in/download/report"}


def shcportal_get_nutrient_values(state, **kw):
    """Retrieves specific nutrient analysis values."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "report_id": kw.get("report_id"), "nutrients": {"nitrogen": 280, "phosphorus": 22, "potassium": 310, "organic_carbon": 0.55, "ph": 6.8}}


def shcportal_get_fertilizer_recommendation(state, **kw):
    """Generates fertilizer recommendations based on SHC results."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "report_id": kw.get("report_id"), "crop_type": kw.get("crop_type"), "recommendations": [{"fertilizer": "Urea", "qty_kg_per_ha": 120}, {"fertilizer": "DAP", "qty_kg_per_ha": 60}]}


def shcportal_get_historical_reports(state, **kw):
    """Retrieves all historical SHC reports."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    return {"status": "success", "reports": [{"report_id": "SHCR-00000001", "year": 2024}, {"report_id": "SHCR-00000002", "year": 2022}]}


def shcportal_filter_reports_by_land(state, **kw):
    """Filters SHC reports for a specific land parcel."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    return {"status": "success", "land_parcel_id": kw.get("land_parcel_id"), "reports": [{"report_id": "SHCR-00000001", "year": 2024}]}


def shcportal_get_lab_details(state, **kw):
    """Returns lab details for the sample."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "sample_id": kw.get("sample_id"), "lab_name": "District Soil Testing Lab", "turnaround_days": 15}


def shcportal_raise_grievance(state, **kw):
    """Raises SHC Portal grievance."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("report_not_found", "incorrect_values", "lab_delay", "wrong_land_mapping", "download_issue")
    cat = kw.get("grievance_category")
    if cat not in cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {cats}")
    if not kw.get("description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("SHCPORTAL-GRV-")
    state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}


def shcportal_track_grievance_status(state, **kw):
    """Tracks SHC Portal grievance."""
    _val_session(kw.get("session_token"))
    gid = kw.get("grievance_id")
    if not gid:
        return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending"}


STUBS = {
    "shcportal_generate_otp": shcportal_generate_otp,
    "shcportal_verify_otp": shcportal_verify_otp,
    "shcportal_search_reports": shcportal_search_reports,
    "shcportal_get_report_details": shcportal_get_report_details,
    "shcportal_check_sample_status": shcportal_check_sample_status,
    "shcportal_download_report": shcportal_download_report,
    "shcportal_get_nutrient_values": shcportal_get_nutrient_values,
    "shcportal_get_fertilizer_recommendation": shcportal_get_fertilizer_recommendation,
    "shcportal_get_historical_reports": shcportal_get_historical_reports,
    "shcportal_filter_reports_by_land": shcportal_filter_reports_by_land,
    "shcportal_get_lab_details": shcportal_get_lab_details,
    "shcportal_raise_grievance": shcportal_raise_grievance,
    "shcportal_track_grievance_status": shcportal_track_grievance_status,
}
