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
    "session_token": None,               # PMFBY-TKN-XXXXXXXX
    "eligibility_status": None,           # 'eligible', 'not_eligible'
    "policy_id": None,
    "policy_status": None,               # 'not_enrolled','enrolled','active','expired'
    "premium_calculated": False,
    "premium_paid": False,
    "claim_id": None,
    "claim_status": None,                # 'not_reported','reported','submitted','under_review','approved','rejected','compensated'
    "survey_status": None,               # 'not_started','in_progress','completed'
    "payment_status": None,              # 'pending','initiated','completed','failed'
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
    if not isinstance(v, str) or not re.fullmatch(r"PMFBY-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match PMFBY-TKN-XXXXXXXX")

def _gen_token():
    return "PMFBY-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def _gen_id(prefix):
    return prefix + "".join(random.choices(string.digits, k=8))


def pmfby_generate_otp(state: dict, **kwargs) -> dict:
    """Sends OTP for PMFBY authentication.
    Reads: nothing
    Mutates: otp_sent
    """
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    m = kwargs.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m):
        raise ToolValidationError("mobile_number", m, "Must be exactly 10 digits")
    state["otp_sent"] = True
    return {"status": "success", "message": "OTP sent to registered mobile number"}


def pmfby_verify_otp(state: dict, **kwargs) -> dict:
    """Verifies OTP and returns session_token.
    Reads: otp_sent
    Mutates: otp_verified, session_token
    """
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    _validate_otp(kwargs.get("otp"))
    if not state.get("otp_sent"):
        return {"status": "error", "code": "OTP_NOT_SENT", "message": "OTP not generated. Call pmfby_generate_otp first."}
    token = _gen_token()
    state["otp_verified"] = True
    state["session_token"] = token
    return {"status": "success", "session_token": token}


def pmfby_check_eligibility(state: dict, **kwargs) -> dict:
    """Checks eligibility for PMFBY enrollment.
    Reads: session_token
    Mutates: eligibility_status
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    valid_crops = ("paddy", "wheat", "maize", "cotton", "pulses", "oilseeds")
    crop = kwargs.get("crop_type")
    if crop not in valid_crops:
        raise ToolValidationError("crop_type", crop, f"Must be one of {valid_crops}")
    state["eligibility_status"] = "eligible"
    return {"status": "success", "eligibility_status": "eligible", "crop_type": crop}


def pmfby_get_season_window(state: dict, **kwargs) -> dict:
    """Returns enrollment window dates for current season.
    Reads: session_token
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    return {
        "status": "success",
        "state": kwargs.get("state"),
        "season": "kharif",
        "enrollment_start": "2024-04-01",
        "enrollment_end": "2024-07-31",
    }


def pmfby_enroll_policy(state: dict, **kwargs) -> dict:
    """Enrolls farmer in PMFBY crop insurance.
    Reads: session_token, eligibility_status, policy_status
    Mutates: policy_id, policy_status
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    if state.get("eligibility_status") != "eligible":
        return {"status": "error", "code": "NOT_ELIGIBLE", "message": "Check eligibility first."}
    if state.get("policy_status") in ("enrolled", "active"):
        return {"status": "error", "code": "DUPLICATE_ENROLLMENT", "message": "Already enrolled."}
    valid_crops = ("paddy", "wheat", "maize", "cotton", "pulses", "oilseeds")
    crop = kwargs.get("crop_type")
    if crop not in valid_crops:
        raise ToolValidationError("crop_type", crop, f"Must be one of {valid_crops}")
    pid = _gen_id("PMFBY-POL-")
    state["policy_id"] = pid
    state["policy_status"] = "enrolled"
    state["claim_status"] = "not_reported"
    return {"status": "success", "policy_id": pid, "policy_status": "enrolled"}


def pmfby_calculate_premium(state: dict, **kwargs) -> dict:
    """Calculates insurance premium.
    Reads: session_token, policy_status
    Mutates: premium_calculated
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("policy_status") != "enrolled":
        return {"status": "error", "code": "NOT_ENROLLED", "message": "Policy must be enrolled."}
    state["premium_calculated"] = True
    return {
        "status": "success",
        "policy_id": kwargs.get("policy_id"),
        "total_premium": 5000,
        "farmer_share": 1000,
        "government_subsidy": 4000,
    }


def pmfby_pay_premium(state: dict, **kwargs) -> dict:
    """Processes premium payment.
    Reads: session_token, policy_status
    Mutates: policy_status, premium_paid
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("policy_status") != "enrolled":
        return {"status": "error", "code": "NOT_ENROLLED", "message": "Policy must be enrolled."}
    valid_modes = ("upi", "netbanking", "debit_card")
    mode = kwargs.get("payment_mode")
    if mode not in valid_modes:
        raise ToolValidationError("payment_mode", mode, f"Must be one of {valid_modes}")
    state["policy_status"] = "active"
    state["premium_paid"] = True
    return {"status": "success", "policy_status": "active", "payment_mode": mode}


def pmfby_get_policy_status(state: dict, **kwargs) -> dict:
    """Retrieves current policy status and details.
    Reads: session_token, policy_status
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    return {
        "status": "success",
        "policy_id": kwargs.get("policy_id"),
        "policy_status": state.get("policy_status", "not_enrolled"),
        "premium_paid": state.get("premium_paid", False),
    }


def pmfby_report_crop_loss(state: dict, **kwargs) -> dict:
    """Reports a crop loss event.
    Reads: session_token, policy_status
    Mutates: claim_id, claim_status
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("policy_status") != "active":
        return {"status": "error", "code": "POLICY_NOT_ACTIVE", "message": "Policy must be active."}
    valid_loss = ("drought", "flood", "pest_attack", "cyclone", "unseasonal_rainfall")
    lt = kwargs.get("loss_type")
    if lt not in valid_loss:
        raise ToolValidationError("loss_type", lt, f"Must be one of {valid_loss}")
    cid = _gen_id("PMFBY-CLM-")
    state["claim_id"] = cid
    state["claim_status"] = "reported"
    return {"status": "success", "claim_id": cid, "claim_status": "reported"}


def pmfby_submit_claim(state: dict, **kwargs) -> dict:
    """Submits formal insurance claim.
    Reads: session_token, claim_status
    Mutates: claim_status
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("claim_status") != "reported":
        return {"status": "error", "code": "NOT_REPORTED", "message": "Loss must be reported first."}
    state["claim_status"] = "submitted"
    return {"status": "success", "claim_status": "submitted", "claim_id": kwargs.get("claim_id")}


def pmfby_track_claim_status(state: dict, **kwargs) -> dict:
    """Tracks claim status.
    Reads: session_token, claim_status
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    return {
        "status": "success",
        "claim_id": kwargs.get("claim_id"),
        "claim_status": state.get("claim_status", "not_reported"),
    }


def pmfby_track_survey_status(state: dict, **kwargs) -> dict:
    """Tracks field survey status for a claim.
    Reads: session_token, survey_status
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    return {
        "status": "success",
        "claim_id": kwargs.get("claim_id"),
        "survey_status": state.get("survey_status", "not_started"),
    }


def pmfby_track_compensation(state: dict, **kwargs) -> dict:
    """Tracks compensation payment status.
    Reads: session_token, claim_status, payment_status
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("claim_status") not in ("approved", "compensated"):
        return {"status": "error", "code": "NOT_APPROVED", "message": "Claim must be approved."}
    return {
        "status": "success",
        "claim_id": kwargs.get("claim_id"),
        "payment_status": state.get("payment_status", "pending"),
    }


def pmfby_raise_grievance(state: dict, **kwargs) -> dict:
    """Raises a PMFBY grievance.
    Reads: session_token
    Mutates: grievance_id
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    valid_cats = ("claim_rejected", "payment_delay", "incorrect_assessment", "policy_issue", "enrollment_failure")
    cat = kwargs.get("grievance_category")
    if cat not in valid_cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {valid_cats}")
    if not kwargs.get("description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description cannot be empty."}
    gid = _gen_id("PMFBY-GRV-")
    state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}


def pmfby_track_grievance_status(state: dict, **kwargs) -> dict:
    """Tracks a PMFBY grievance.
    Reads: session_token
    Mutates: NONE
    """
    _validate_session(kwargs.get("session_token"))
    gid = kwargs.get("grievance_id")
    if not gid:
        return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending", "remarks": None}


STUBS = {
    "pmfby_generate_otp": pmfby_generate_otp,
    "pmfby_verify_otp": pmfby_verify_otp,
    "pmfby_check_eligibility": pmfby_check_eligibility,
    "pmfby_get_season_window": pmfby_get_season_window,
    "pmfby_enroll_policy": pmfby_enroll_policy,
    "pmfby_calculate_premium": pmfby_calculate_premium,
    "pmfby_pay_premium": pmfby_pay_premium,
    "pmfby_get_policy_status": pmfby_get_policy_status,
    "pmfby_report_crop_loss": pmfby_report_crop_loss,
    "pmfby_submit_claim": pmfby_submit_claim,
    "pmfby_track_claim_status": pmfby_track_claim_status,
    "pmfby_track_survey_status": pmfby_track_survey_status,
    "pmfby_track_compensation": pmfby_track_compensation,
    "pmfby_raise_grievance": pmfby_raise_grievance,
    "pmfby_track_grievance_status": pmfby_track_grievance_status,
}
