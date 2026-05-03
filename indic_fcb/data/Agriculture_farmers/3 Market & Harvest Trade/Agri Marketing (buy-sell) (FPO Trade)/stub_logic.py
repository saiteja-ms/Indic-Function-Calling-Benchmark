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
    "listing_id": None,
    "listing_status": None,
    "order_id": None,
    "order_status": None,
    "payment_status": None,
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
    if not isinstance(v, str) or not re.fullmatch(r"AGRIMARKET-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match AGRIMARKET-TKN-XXXXXXXX")

def _gen_token():
    return "AGRIMARKET-TKN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def _gen_id(pfx):
    return pfx + "".join(random.choices(string.digits, k=8))


def agrimarket_generate_otp(state, **kw):
    """Sends OTP for Agri Marketing authentication."""
    _val_aadhaar(kw.get("aadhaar_number"))
    m = kw.get("mobile_number")
    if not isinstance(m, str) or not re.fullmatch(r"\d{10}", m):
        raise ToolValidationError("mobile_number", m, "Must be 10 digits")
    state["otp_sent"] = True
    return {"status": "success", "message": "OTP sent to registered mobile number"}


def agrimarket_verify_otp(state, **kw):
    """Verifies OTP and returns session_token."""
    _val_aadhaar(kw.get("aadhaar_number"))
    _val_otp(kw.get("otp"))
    if not state.get("otp_sent"):
        return {"status": "error", "code": "OTP_NOT_SENT", "message": "Call agrimarket_generate_otp first."}
    token = _gen_token()
    state["otp_verified"] = True
    state["session_token"] = token
    return {"status": "success", "session_token": token}


def agrimarket_create_listing(state, **kw):
    """Creates a new crop listing for sale."""
    _val_session(kw.get("session_token"))
    valid_types = ("fixed_price", "auction")
    lt = kw.get("listing_type")
    if lt not in valid_types:
        raise ToolValidationError("listing_type", lt, f"Must be one of {valid_types}")
    lid = _gen_id("AGLST-")
    state["listing_id"] = lid
    state["listing_status"] = "active"
    return {"status": "success", "listing_id": lid, "listing_status": "active"}


def agrimarket_search_listings(state, **kw):
    """Searches available crop listings."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "listings": [{"listing_id": "AGLST-00000001", "commodity_type": kw.get("commodity_type", "paddy"), "price_per_unit": 2200}]}


def agrimarket_get_listing_details(state, **kw):
    """Retrieves full listing details."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "listing_id": kw.get("listing_id"), "listing_status": state.get("listing_status", "active"), "commodity_type": "paddy", "price_per_unit": 2200}


def agrimarket_update_listing(state, **kw):
    """Updates an existing listing."""
    _val_session(kw.get("session_token"))
    if kw.get("listing_status"):
        state["listing_status"] = kw["listing_status"]
    return {"status": "success", "listing_id": kw.get("listing_id"), "message": "Listing updated."}


def agrimarket_place_order(state, **kw):
    """Places an order on an active listing."""
    _val_session(kw.get("session_token"))
    oid = _gen_id("AGORD-")
    state["order_id"] = oid
    state["order_status"] = "created"
    return {"status": "success", "order_id": oid, "order_status": "created"}


def agrimarket_track_order(state, **kw):
    """Tracks order status."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "order_id": kw.get("order_id"), "order_status": state.get("order_status", "created")}


def agrimarket_track_payment(state, **kw):
    """Tracks payment status for an order."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "order_id": kw.get("order_id"), "payment_status": state.get("payment_status", "pending")}


def agrimarket_bid_on_listing(state, **kw):
    """Places a bid on an auction-type listing."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "listing_id": kw.get("listing_id"), "bid_amount": kw.get("bid_amount"), "bid_status": "placed"}


def agrimarket_cancel_order(state, **kw):
    """Cancels an existing order."""
    _val_session(kw.get("session_token"))
    if state.get("order_status") in ("dispatched", "delivered", "completed"):
        return {"status": "error", "code": "CANNOT_CANCEL", "message": "Cannot cancel after dispatch."}
    state["order_status"] = "cancelled"
    return {"status": "success", "order_status": "cancelled"}


def agrimarket_track_delivery(state, **kw):
    """Tracks delivery status for dispatched orders."""
    _val_session(kw.get("session_token"))
    if state.get("order_status") not in ("dispatched", "delivered"):
        return {"status": "error", "code": "NOT_DISPATCHED", "message": "Order not dispatched yet."}
    return {"status": "success", "order_id": kw.get("order_id"), "delivery_status": "in_transit"}


def agrimarket_raise_grievance(state, **kw):
    """Raises Agri Marketing grievance."""
    _val_session(kw.get("session_token"))
    cats = ("payment_issue", "order_not_delivered", "wrong_quality", "price_mismatch", "listing_issue")
    cat = kw.get("grievance_category")
    if cat not in cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {cats}")
    if not kw.get("description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("AGRIMARKET-GRV-")
    state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}


def agrimarket_track_grievance_status(state, **kw):
    """Tracks grievance status."""
    _val_session(kw.get("session_token"))
    gid = kw.get("grievance_id")
    if not gid:
        return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending"}


STUBS = {
    "agrimarket_generate_otp": agrimarket_generate_otp,
    "agrimarket_verify_otp": agrimarket_verify_otp,
    "agrimarket_create_listing": agrimarket_create_listing,
    "agrimarket_search_listings": agrimarket_search_listings,
    "agrimarket_get_listing_details": agrimarket_get_listing_details,
    "agrimarket_update_listing": agrimarket_update_listing,
    "agrimarket_place_order": agrimarket_place_order,
    "agrimarket_track_order": agrimarket_track_order,
    "agrimarket_track_payment": agrimarket_track_payment,
    "agrimarket_bid_on_listing": agrimarket_bid_on_listing,
    "agrimarket_cancel_order": agrimarket_cancel_order,
    "agrimarket_track_delivery": agrimarket_track_delivery,
    "agrimarket_raise_grievance": agrimarket_raise_grievance,
    "agrimarket_track_grievance_status": agrimarket_track_grievance_status,
}
