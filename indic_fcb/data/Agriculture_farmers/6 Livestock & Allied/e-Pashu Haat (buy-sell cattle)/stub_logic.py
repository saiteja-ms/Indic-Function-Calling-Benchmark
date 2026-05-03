import re, random, string

class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field, self.value, self.reason = field, value, reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")

INITIAL_STATE = {
    "otp_sent": False, "otp_verified": False, "session_token": None,
    "livestock_id": None, "listing_id": None, "listing_status": None,
    "order_id": None, "order_status": None, "verification_status": None,
    "grievance_id": None,
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
    if not isinstance(v, str) or not re.fullmatch(r"EPASHU-TKN-[A-Za-z0-9]{8}", v): raise ToolValidationError("session_token", v, "Must match EPASHU-TKN-XXXXXXXX")
def _gen_token(): return "EPASHU-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
def _gen_id(pfx): return pfx + "".join(random.choices(string.digits, k=8))

def epashu_generate_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m): raise ToolValidationError("mobile_number", m, "Must be 10 digits")
    state["otp_sent"] = True; return {"status": "success", "message": "OTP sent"}

def epashu_verify_otp(state, **kw):
    _val_aadhaar(kw.get("aadhaar_number")); _val_otp(kw.get("otp"))
    if not state.get("otp_sent"): return {"status": "error", "code": "OTP_NOT_SENT", "message": "Call epashu_generate_otp first."}
    token = _gen_token(); state["otp_verified"] = True; state["session_token"] = token
    return {"status": "success", "session_token": token}

def epashu_register_livestock(state, **kw):
    _val_session(kw.get("session_token"))
    lid = _gen_id("EPASHU-LVS-"); state["livestock_id"] = lid
    return {"status": "success", "livestock_id": lid}

def epashu_create_listing(state, **kw):
    _val_session(kw.get("session_token"))
    if not state.get("livestock_id"): return {"status": "error", "code": "NO_LIVESTOCK", "message": "Register livestock first."}
    lstid = _gen_id("EPASHU-LST-"); state["listing_id"] = lstid; state["listing_status"] = "active"
    return {"status": "success", "listing_id": lstid, "listing_status": "active"}

def epashu_search_listings(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "listings": [{"listing_id": "EPASHU-LST-00000001", "animal_type": kw.get("animal_type", "cow"), "price": 45000}]}

def epashu_get_listing_details(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "listing_id": kw.get("listing_id"), "listing_status": state.get("listing_status", "active"), "price": 45000}

def epashu_verify_livestock(state, **kw):
    _val_session(kw.get("session_token"))
    state["verification_status"] = "verified"
    return {"status": "success", "livestock_id": kw.get("livestock_id"), "verification_status": "verified"}

def epashu_place_order(state, **kw):
    _val_session(kw.get("session_token"))
    oid = _gen_id("EPASHU-ORD-"); state["order_id"] = oid; state["order_status"] = "requested"
    return {"status": "success", "order_id": oid, "order_status": "requested"}

def epashu_track_order(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "order_id": kw.get("order_id"), "order_status": state.get("order_status", "requested")}

def epashu_transfer_ownership(state, **kw):
    _val_session(kw.get("session_token"))
    state["order_status"] = "transferred"
    return {"status": "success", "order_id": kw.get("order_id"), "order_status": "transferred"}

def epashu_update_listing(state, **kw):
    _val_session(kw.get("session_token"))
    if kw.get("listing_status"): state["listing_status"] = kw["listing_status"]
    return {"status": "success", "listing_id": kw.get("listing_id"), "message": "Listing updated."}

def epashu_track_logistics(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "order_id": kw.get("order_id"), "logistics_status": "not_started"}

def epashu_cancel_order(state, **kw):
    _val_session(kw.get("session_token"))
    if state.get("order_status") in ("payment_done", "transferred", "completed"): return {"status": "error", "code": "CANNOT_CANCEL", "message": "Cannot cancel after payment."}
    state["order_status"] = "cancelled"
    return {"status": "success", "order_status": "cancelled"}

def epashu_negotiate_price(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "listing_id": kw.get("listing_id"), "offered_price": kw.get("offered_price"), "negotiation_status": "sent"}

def epashu_raise_grievance(state, **kw):
    _val_session(kw.get("session_token"))
    cats = ("fraudulent_listing", "payment_issue", "delivery_issue", "incorrect_details", "ownership_issue")
    if kw.get("grievance_category") not in cats: raise ToolValidationError("grievance_category", kw.get("grievance_category"), f"Must be one of {cats}")
    if not kw.get("description"): return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("EPASHU-GRV-"); state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}

def epashu_track_grievance_status(state, **kw):
    _val_session(kw.get("session_token"))
    gid = kw.get("grievance_id")
    if not gid: return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending"}

STUBS = {
    "epashu_generate_otp": epashu_generate_otp, "epashu_verify_otp": epashu_verify_otp,
    "epashu_register_livestock": epashu_register_livestock, "epashu_create_listing": epashu_create_listing,
    "epashu_search_listings": epashu_search_listings, "epashu_get_listing_details": epashu_get_listing_details,
    "epashu_verify_livestock": epashu_verify_livestock, "epashu_place_order": epashu_place_order,
    "epashu_track_order": epashu_track_order, "epashu_transfer_ownership": epashu_transfer_ownership,
    "epashu_update_listing": epashu_update_listing, "epashu_track_logistics": epashu_track_logistics,
    "epashu_cancel_order": epashu_cancel_order, "epashu_negotiate_price": epashu_negotiate_price,
    "epashu_raise_grievance": epashu_raise_grievance, "epashu_track_grievance_status": epashu_track_grievance_status,
}
