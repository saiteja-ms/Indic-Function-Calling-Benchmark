import re, random, string
from datetime import date


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
    "otp_sent": False,                # True after generate_otp
    "otp_verified": False,            # True after verify_otp
    "session_token": None,            # PMKISAN-TKN-XXXXXXXX
    "registration_status": None,      # 'not_registered', 'registered', 'verified'
    "ekyc_status": None,              # 'not_started', 'completed', 'failed'
    "eligibility_status": None,       # 'eligible', 'ineligible', 'rejected'
    "beneficiary_id": None,           # unique beneficiary identifier
    "payment_status": None,           # 'not_initiated', 'pending', 'credited', 'failed'
    "installment_status": None,       # 'due', 'processed', 'credited', 'failed'
    "grievance_id": None,             # grievance identifier
    "bank_account_number": None,      # bank account
    "ifsc_code": None,                # IFSC code
    "land_verified": False,           # True after land validation
    "payment_history": [],            # list of payment records
    "transaction_reference": None,    # transaction ref
}



# ── PERSONA STATES ──────────────────────────────
# Each persona is a filled INITIAL_STATE instance.
# Pass one of these to StubContext() at scenario start.

PERSONA_A = {"otp_sent": False, "otp_verified": False, "session_token": None, "registration_status": None, "ekyc_status": None, "eligibility_status": None, "beneficiary_id": None, "payment_status": None, "installment_status": None, "grievance_id": None, "bank_account_number": None, "ifsc_code": None, "land_verified": False, "payment_history": [], "transaction_reference": None}
PERSONA_B = {"otp_sent": True, "otp_verified": True, "session_token": "PMKISAN-TKN-AB12CD34", "registration_status": "registered", "ekyc_status": "not_started", "eligibility_status": "eligible", "beneficiary_id": "PMKISAN-BEN-10000001", "payment_status": "credited", "installment_status": "due", "grievance_id": None, "bank_account_number": "00112233445566", "ifsc_code": "SBIN0001234", "land_verified": True, "payment_history": [{'installment': 1, 'amount': 2000, 'date': '2024-04-15', 'status': 'credited'}, {'installment': 2, 'amount': 2000, 'date': '2024-08-10', 'status': 'credited'}], "transaction_reference": None}
PERSONA_C = {"otp_sent": True, "otp_verified": True, "session_token": "PMKISAN-TKN-EF56GH78", "registration_status": "verified", "ekyc_status": "completed", "eligibility_status": "eligible", "beneficiary_id": "PMKISAN-BEN-10000002", "payment_status": "credited", "installment_status": "credited", "grievance_id": None, "bank_account_number": "33445566778899", "ifsc_code": "PUNB0012345", "land_verified": True, "payment_history": [{'installment': 1, 'amount': 2000, 'date': '2024-04-15', 'status': 'credited'}, {'installment': 2, 'amount': 2000, 'date': '2024-08-10', 'status': 'credited'}, {'installment': 3, 'amount': 2000, 'date': '2024-12-05', 'status': 'credited'}], "transaction_reference": "TXN-PMKISAN-20241205"}
PERSONA_D = {"otp_sent": True, "otp_verified": True, "session_token": "PMKISAN-TKN-IJ90KL12", "registration_status": "registered", "ekyc_status": "completed", "eligibility_status": "eligible", "beneficiary_id": "PMKISAN-BEN-10000003", "payment_status": "failed", "installment_status": "failed", "grievance_id": None, "bank_account_number": "55667788990011", "ifsc_code": "HDFC0001234", "land_verified": True, "payment_history": [{'installment': 1, 'amount': 2000, 'date': '2024-04-15', 'status': 'credited'}, {'installment': 2, 'amount': 2000, 'date': '2024-08-10', 'status': 'credited'}, {'installment': 3, 'amount': 2000, 'date': None, 'status': 'failed', 'rejection_reason': 'NAME_MISMATCH'}], "transaction_reference": "TXN-PMKISAN-FAIL-001"}
PERSONA_E = {"otp_sent": True, "otp_verified": True, "session_token": "PMKISAN-TKN-MN34OP56", "registration_status": "verified", "ekyc_status": "completed", "eligibility_status": "eligible", "beneficiary_id": "PMKISAN-BEN-10000004", "payment_status": "pending", "installment_status": "due", "grievance_id": None, "bank_account_number": "77889900112233", "ifsc_code": "MAHB0001234", "land_verified": True, "payment_history": [{'installment': 1, 'amount': 2000, 'date': '2024-04-15', 'status': 'credited'}, {'installment': 2, 'amount': 2000, 'date': None, 'status': 'pending'}], "transaction_reference": None}
PERSONA_F = {"otp_sent": True, "otp_verified": True, "session_token": "PMKISAN-TKN-QR78ST90", "registration_status": "verified", "ekyc_status": "completed", "eligibility_status": "eligible", "beneficiary_id": "PMKISAN-BEN-10000005", "payment_status": "pending", "installment_status": "due", "grievance_id": "PMKISAN-GRV-20240301", "bank_account_number": "99001122334455", "ifsc_code": "BKID0001234", "land_verified": True, "payment_history": [{'installment': 1, 'amount': 2000, 'date': '2024-04-15', 'status': 'credited'}, {'installment': 2, 'amount': 2000, 'date': '2024-08-10', 'status': 'credited'}, {'installment': 3, 'amount': 2000, 'date': None, 'status': 'pending'}], "transaction_reference": None}
PERSONA_G = {"otp_sent": True, "otp_verified": True, "session_token": "PMKISAN-TKN-UV12WX34", "registration_status": "registered", "ekyc_status": "completed", "eligibility_status": "eligible", "beneficiary_id": "PMKISAN-BEN-10000006", "payment_status": "credited", "installment_status": "credited", "grievance_id": None, "bank_account_number": "11223344556677", "ifsc_code": "ANDB0001234", "land_verified": True, "payment_history": [{'installment': 1, 'amount': 2000, 'date': '2024-04-15', 'status': 'credited'}, {'installment': 2, 'amount': 2000, 'date': '2024-08-10', 'status': 'credited'}], "transaction_reference": None}
PERSONA_H = {"otp_sent": True, "otp_verified": True, "session_token": "PMKISAN-TKN-YZ56AB78", "registration_status": "registered", "ekyc_status": "completed", "eligibility_status": "ineligible", "beneficiary_id": "PMKISAN-BEN-10000007", "payment_status": "not_initiated", "installment_status": None, "grievance_id": None, "bank_account_number": "88990011223344", "ifsc_code": "SBIN0005678", "land_verified": False, "payment_history": [], "transaction_reference": None}

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
    def __init__(self, state: dict):
        self.state    = state.copy()
        self.call_log = []

    def call(self, tool_name: str, **kwargs) -> dict:
        self.call_log.append({
            "tool": tool_name,
            "args": kwargs
        })
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

def _validate_mobile(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{10}", v):
        raise ToolValidationError("mobile_number", v, "Must be exactly 10 digits")

def _validate_otp(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{6}", v):
        raise ToolValidationError("otp", v, "Must be exactly 6 digits")

def _validate_session(v):
    if not isinstance(v, str) or not re.fullmatch(r"PMKISAN-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match PMKISAN-TKN-XXXXXXXX")

def _gen_token():
    return "PMKISAN-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def _gen_id(prefix):
    return prefix + "".join(random.choices(string.digits, k=8))


def pmkisan_generate_otp(state: dict, **kwargs) -> dict:
    """Sends OTP for PM-KISAN authentication.
    Reads: nothing
    Mutates: otp_sent
    Raises: ToolValidationError if aadhaar or mobile invalid
    """
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    _validate_mobile(kwargs.get("mobile_number"))
    state["otp_sent"] = True
    return {"status": "success", "message": "OTP sent to registered mobile number"}


def pmkisan_verify_otp(state: dict, **kwargs) -> dict:
    """Verifies OTP and returns session_token.
    Reads: otp_sent
    Mutates: otp_verified, session_token
    Raises: ToolValidationError if aadhaar or otp invalid
    """
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    _validate_otp(kwargs.get("otp"))
    if not state.get("otp_sent"):
        return {"status": "error", "code": "OTP_NOT_SENT", "message": "OTP not generated. Call pmkisan_generate_otp first."}
    token = _gen_token()
    state["otp_verified"] = True
    state["session_token"] = token
    return {"status": "success", "session_token": token}


def pmkisan_register_farmer(state: dict, **kwargs) -> dict:
    """Registers a new farmer for PM-KISAN benefits.
    Reads: session_token, registration_status
    Mutates: registration_status, beneficiary_id, bank_account_number, ifsc_code
    Raises: ToolValidationError if session_token or aadhaar invalid
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    if state.get("registration_status") in ("registered", "verified"):
        return {"status": "error", "code": "DUPLICATE_REGISTRATION", "message": "Farmer already registered."}
    bid = _gen_id("PMKISAN-BEN-")
    state["registration_status"] = "registered"
    state["beneficiary_id"] = bid
    state["ekyc_status"] = "not_started"
    state["bank_account_number"] = kwargs.get("bank_account_number")
    state["ifsc_code"] = kwargs.get("ifsc_code")
    return {"status": "success", "beneficiary_id": bid, "registration_status": "registered"}


def pmkisan_check_eligibility(state: dict, **kwargs) -> dict:
    """Checks farmer eligibility for PM-KISAN.
    Reads: session_token, registration_status
    Mutates: eligibility_status
    Raises: ToolValidationError if session_token or aadhaar invalid
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    if state.get("registration_status") not in ("registered", "verified"):
        return {"status": "error", "code": "NOT_REGISTERED", "message": "Farmer not registered."}
    state["eligibility_status"] = "eligible"
    return {"status": "success", "eligibility_status": "eligible"}


def pmkisan_complete_ekyc(state: dict, **kwargs) -> dict:
    """Completes OTP-based eKYC for PM-KISAN.
    Reads: session_token, ekyc_status
    Mutates: ekyc_status
    Raises: ToolValidationError if session_token, aadhaar, or ekyc_otp invalid
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    _validate_otp(kwargs.get("ekyc_otp"))
    if state.get("ekyc_status") == "completed":
        return {"status": "error", "code": "EKYC_ALREADY_DONE", "message": "eKYC already completed."}
    state["ekyc_status"] = "completed"
    return {"status": "success", "ekyc_status": "completed"}


def pmkisan_get_beneficiary_status(state: dict, **kwargs) -> dict:
    """Retrieves current beneficiary status.
    Reads: session_token, registration_status, ekyc_status, eligibility_status, bank_account_number
    Mutates: NONE
    Raises: ToolValidationError if session_token or aadhaar invalid
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    if not state.get("registration_status"):
        return {"status": "success", "registration_status": "not_registered"}
    return {
        "status": "success",
        "registration_status": state.get("registration_status"),
        "ekyc_status": state.get("ekyc_status"),
        "eligibility_status": state.get("eligibility_status"),
        "beneficiary_id": state.get("beneficiary_id"),
        "bank_account_number": state.get("bank_account_number"),
    }


def pmkisan_get_payment_history(state: dict, **kwargs) -> dict:
    """Retrieves complete payment history.
    Reads: session_token, registration_status, payment_history
    Mutates: NONE
    Raises: ToolValidationError if session_token or aadhaar invalid
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    if not state.get("registration_status"):
        return {"status": "error", "code": "NOT_REGISTERED", "message": "Farmer not registered."}
    return {"status": "success", "payment_history": state.get("payment_history", [])}


def pmkisan_track_installment_status(state: dict, **kwargs) -> dict:
    """Tracks status of a specific installment.
    Reads: session_token, registration_status
    Mutates: NONE
    Raises: ToolValidationError if session_token or aadhaar invalid
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    if not state.get("registration_status"):
        return {"status": "error", "code": "NOT_REGISTERED", "message": "Farmer not registered."}
    inst_num = kwargs.get("installment_number", 1)
    fy = kwargs.get("financial_year", "2024-25")
    return {
        "status": "success",
        "installment_number": inst_num,
        "financial_year": fy,
        "installment_status": state.get("installment_status", "due"),
        "amount": 2000,
    }


def pmkisan_update_bank_details(state: dict, **kwargs) -> dict:
    """Updates bank account details.
    Reads: session_token
    Mutates: bank_account_number, ifsc_code
    Raises: ToolValidationError if session_token or aadhaar invalid
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    state["bank_account_number"] = kwargs.get("bank_account_number")
    state["ifsc_code"] = kwargs.get("ifsc_code")
    return {"status": "success", "message": "Bank details updated successfully."}


def pmkisan_track_payment(state: dict, **kwargs) -> dict:
    """Tracks payment processing status.
    Reads: session_token, payment_status
    Mutates: NONE
    Raises: ToolValidationError if session_token invalid
    """
    _validate_session(kwargs.get("session_token"))
    return {
        "status": "success",
        "beneficiary_id": kwargs.get("beneficiary_id"),
        "payment_status": state.get("payment_status", "not_initiated"),
        "transaction_reference": kwargs.get("transaction_reference"),
    }


def pmkisan_validate_land_records(state: dict, **kwargs) -> dict:
    """Validates farmer's land ownership records.
    Reads: session_token
    Mutates: land_verified
    Raises: ToolValidationError if session_token or aadhaar invalid
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    state["land_verified"] = True
    return {"status": "success", "verification_status": "verified", "state": kwargs.get("state"), "district": kwargs.get("district")}


def pmkisan_resolve_payment_failure(state: dict, **kwargs) -> dict:
    """Initiates resolution for failed PM-KISAN payment.
    Reads: session_token, payment_status
    Mutates: payment_status
    Raises: ToolValidationError if session_token invalid
    """
    _validate_session(kwargs.get("session_token"))
    if state.get("payment_status") != "failed":
        return {"status": "error", "code": "NO_FAILED_PAYMENT", "message": "No failed payment found."}
    state["payment_status"] = "pending"
    return {"status": "success", "message": "Resolution initiated.", "transaction_reference": kwargs.get("transaction_reference")}


def pmkisan_get_installment_schedule(state: dict, **kwargs) -> dict:
    """Retrieves installment schedule for the financial year.
    Reads: session_token, registration_status, eligibility_status
    Mutates: NONE
    Raises: ToolValidationError if session_token or aadhaar invalid
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    if not state.get("registration_status"):
        return {"status": "error", "code": "NOT_REGISTERED", "message": "Farmer not registered."}
    fy = kwargs.get("financial_year", "2024-25")
    return {
        "status": "success",
        "financial_year": fy,
        "installments": [
            {"number": 1, "amount": 2000, "period": "Apr-Jul"},
            {"number": 2, "amount": 2000, "period": "Aug-Nov"},
            {"number": 3, "amount": 2000, "period": "Dec-Mar"},
        ],
    }


def pmkisan_resolve_eligibility_ambiguity(state: dict, **kwargs) -> dict:
    """Resolves ambiguous eligibility results.
    Reads: session_token, registration_status, eligibility_status
    Mutates: NONE
    Raises: ToolValidationError if session_token or aadhaar invalid
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    if not state.get("registration_status"):
        return {"status": "error", "code": "NOT_REGISTERED", "message": "Farmer not registered."}
    return {
        "status": "success",
        "eligibility_status": state.get("eligibility_status"),
        "criteria_breakdown": {
            "land_ownership": True,
            "income_tax_payer": False,
            "institutional_landholder": False,
            "government_employee": False,
        },
    }


def pmkisan_raise_grievance(state: dict, **kwargs) -> dict:
    """Raises a PM-KISAN grievance.
    Reads: session_token
    Mutates: grievance_id
    Raises: ToolValidationError if session_token or aadhaar invalid
    """
    _validate_session(kwargs.get("session_token"))
    _validate_aadhaar(kwargs.get("aadhaar_number"))
    valid_cats = ("payment_not_received", "ekyc_issue", "bank_account_issue", "eligibility_issue", "registration_issue")
    cat = kwargs.get("grievance_category")
    if cat not in valid_cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {valid_cats}")
    desc = kwargs.get("description")
    if not desc:
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description cannot be empty."}
    gid = _gen_id("PMKISAN-GRV-")
    state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}


def pmkisan_track_grievance_status(state: dict, **kwargs) -> dict:
    """Tracks a PM-KISAN grievance status.
    Reads: session_token
    Mutates: NONE
    Raises: ToolValidationError if session_token invalid
    """
    _validate_session(kwargs.get("session_token"))
    gid = kwargs.get("grievance_id")
    if not gid:
        return {"status": "error", "code": "INVALID_GRIEVANCE_ID", "message": "Grievance ID is required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending", "remarks": None}


STUBS = {
    "pmkisan_generate_otp": pmkisan_generate_otp,
    "pmkisan_verify_otp": pmkisan_verify_otp,
    "pmkisan_register_farmer": pmkisan_register_farmer,
    "pmkisan_check_eligibility": pmkisan_check_eligibility,
    "pmkisan_complete_ekyc": pmkisan_complete_ekyc,
    "pmkisan_get_beneficiary_status": pmkisan_get_beneficiary_status,
    "pmkisan_get_payment_history": pmkisan_get_payment_history,
    "pmkisan_track_installment_status": pmkisan_track_installment_status,
    "pmkisan_update_bank_details": pmkisan_update_bank_details,
    "pmkisan_track_payment": pmkisan_track_payment,
    "pmkisan_validate_land_records": pmkisan_validate_land_records,
    "pmkisan_resolve_payment_failure": pmkisan_resolve_payment_failure,
    "pmkisan_get_installment_schedule": pmkisan_get_installment_schedule,
    "pmkisan_resolve_eligibility_ambiguity": pmkisan_resolve_eligibility_ambiguity,
    "pmkisan_raise_grievance": pmkisan_raise_grievance,
    "pmkisan_track_grievance_status": pmkisan_track_grievance_status,
}
