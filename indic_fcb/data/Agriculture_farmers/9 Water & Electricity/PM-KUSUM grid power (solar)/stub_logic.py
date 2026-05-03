import re, random, string

class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field, self.value, self.reason = field, value, reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")

INITIAL_STATE = {
    "otp_sent": False, "otp_verified": False, "session_token": None,
    "eligibility_status": None, "application_id": None, "application_status": None,
    "installation_status": None, "plant_id": None, "generation_status": None,
    "grid_status": None, "payment_status": None, "grievance_id": None,
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
    if not isinstance(v, str) or not re.fullmatch(r"\d{12}", v): raise ToolValidationError("aadhaar_number", v, "12 digits")
def _val_otp(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{6}", v): raise ToolValidationError("otp", v, "6 digits")
def _val_session(v):
    if not isinstance(v, str) or not re.fullmatch(r"KUSUMGRID-TKN-[A-Za-z0-9]{8}", v): raise ToolValidationError("session_token", v, "KUSUMGRID-TKN-XXXXXXXX")
def _gen_token(): return "KUSUMGRID-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
def _gen_id(pfx): return pfx + "".join(random.choices(string.digits, k=8))

def pmkusumgrid_generate_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m): raise ToolValidationError("mobile_number", m, "10 digits")
    state["otp_sent"] = True; return {"status": "success", "message": "OTP sent"}

def pmkusumgrid_verify_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number")); _val_otp(kw.get("otp"))
    if not state.get("otp_sent"): return {"status": "error", "code": "OTP_NOT_SENT"}
    t = _gen_token(); state["otp_verified"] = True; state["session_token"] = t
    return {"status": "success", "session_token": t}

def pmkusumgrid_check_eligibility(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    state["eligibility_status"] = "eligible"
    return {"status": "success", "eligibility_status": "eligible"}

def pmkusumgrid_apply_system(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    if state.get("eligibility_status") != "eligible": return {"status": "error", "code": "NOT_ELIGIBLE"}
    aid = _gen_id("KUSUMGRID-APP-"); state["application_id"] = aid; state["application_status"] = "submitted"
    return {"status": "success", "application_id": aid, "application_status": "submitted"}

def pmkusumgrid_track_application_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "application_status": state.get("application_status", "not_applied")}

def pmkusumgrid_track_installation(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "installation_status": state.get("installation_status", "not_started")}

def pmkusumgrid_monitor_generation(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "plant_id": kw.get("plant_id"), "generation_status": state.get("generation_status", "generating"), "daily_kwh": 25}

def pmkusumgrid_track_exported_energy(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "plant_id": kw.get("plant_id"), "units_exported": 750, "tariff_rate": 3.5, "expected_revenue": 2625}

def pmkusumgrid_track_payment(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "payment_status": state.get("payment_status", "not_initiated")}

def pmkusumgrid_report_fault(state, **kw):
    _val_session(kw.get("session_token"))
    valid_faults = ("inverter_failure", "panel_damage", "grid_disconnect", "meter_malfunction", "low_output")
    if kw.get("fault_type") not in valid_faults: raise ToolValidationError("fault_type", kw.get("fault_type"), f"Must be one of {valid_faults}")
    state["generation_status"] = "fault"
    return {"status": "success", "plant_id": kw.get("plant_id"), "generation_status": "fault"}

def pmkusumgrid_get_tariff_details(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "state": kw.get("state"), "tariff_rate": 3.5, "unit": "INR/kWh"}

def pmkusumgrid_calculate_revenue(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "estimated_revenue": 9000, "time_range": kw.get("time_range")}

def pmkusumgrid_get_grid_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "grid_status": state.get("grid_status", "connected")}

def pmkusumgrid_schedule_maintenance(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "plant_id": kw.get("plant_id"), "maintenance_status": "scheduled"}

def pmkusumgrid_raise_grievance(state, **kw):
    _val_session(kw.get("session_token")); _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("installation_delay", "low_generation", "payment_delay", "metering_issue", "system_fault")
    if kw.get("grievance_category") not in cats: raise ToolValidationError("grievance_category", kw.get("grievance_category"), f"Must be one of {cats}")
    if not kw.get("description"): return {"status": "error", "code": "EMPTY_DESCRIPTION"}
    gid = _gen_id("KUSUMGRID-GRV-"); state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}

def pmkusumgrid_track_grievance_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "grievance_id": kw.get("grievance_id"), "resolution_status": "pending"}

STUBS = {
    "pmkusumgrid_generate_otp": pmkusumgrid_generate_otp, "pmkusumgrid_verify_otp": pmkusumgrid_verify_otp,
    "pmkusumgrid_check_eligibility": pmkusumgrid_check_eligibility, "pmkusumgrid_apply_system": pmkusumgrid_apply_system,
    "pmkusumgrid_track_application_status": pmkusumgrid_track_application_status,
    "pmkusumgrid_track_installation": pmkusumgrid_track_installation,
    "pmkusumgrid_monitor_generation": pmkusumgrid_monitor_generation,
    "pmkusumgrid_track_exported_energy": pmkusumgrid_track_exported_energy,
    "pmkusumgrid_track_payment": pmkusumgrid_track_payment, "pmkusumgrid_report_fault": pmkusumgrid_report_fault,
    "pmkusumgrid_get_tariff_details": pmkusumgrid_get_tariff_details,
    "pmkusumgrid_calculate_revenue": pmkusumgrid_calculate_revenue,
    "pmkusumgrid_get_grid_status": pmkusumgrid_get_grid_status,
    "pmkusumgrid_schedule_maintenance": pmkusumgrid_schedule_maintenance,
    "pmkusumgrid_raise_grievance": pmkusumgrid_raise_grievance,
    "pmkusumgrid_track_grievance_status": pmkusumgrid_track_grievance_status,
}
