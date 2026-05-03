import re, random, string


class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")


INITIAL_STATE = {"session_token": None, "grievance_id": None, "preferred_dealer": None}



# ── PERSONA STATES ──────────────────────────────
# Each persona is a filled INITIAL_STATE instance.
# Pass one of these to StubContext() at scenario start.

PERSONA_A = {"session_token": None, "grievance_id": None, "preferred_dealer": None}
PERSONA_B = {"session_token": "DEALER-TKN-AB12CD34", "grievance_id": None, "preferred_dealer": None}
PERSONA_C = {"session_token": None, "grievance_id": None, "preferred_dealer": None}
PERSONA_D = {"session_token": None, "grievance_id": None, "preferred_dealer": None}
PERSONA_E = {"session_token": "DEALER-TKN-EF56GH78", "grievance_id": None, "preferred_dealer": None}
PERSONA_F = {"session_token": "DEALER-TKN-IJ90KL12", "grievance_id": None, "preferred_dealer": None}
PERSONA_G = {"session_token": None, "grievance_id": None, "preferred_dealer": None}
PERSONA_H = {"session_token": "DEALER-TKN-MN34OP56", "grievance_id": "DEALER-GRV-20000001", "preferred_dealer": None}

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


def _val_session(v):
    if not isinstance(v, str) or not re.fullmatch(r"DEALER-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match DEALER-TKN-XXXXXXXX")
def _gen_id(pfx):
    return pfx + "".join(random.choices(string.digits, k=8))


def dealer_search_by_location(state, **kw):
    """PUBLIC. Searches dealers by location."""
    if not kw.get("location"):
        return {"status": "error", "code": "INVALID_LOCATION", "message": "Location required."}
    return {"status": "success", "dealers": [{"dealer_id": "DLR-001", "name": "Krishi Seeds & Pesticides", "location": kw["location"]}]}

def dealer_filter_by_product(state, **kw):
    """PUBLIC. Filters dealers by product and crop."""
    if not kw.get("location") or not kw.get("product_type"):
        return {"status": "error", "code": "MISSING_PARAMS", "message": "Location and product_type required."}
    return {"status": "success", "dealers": [{"dealer_id": "DLR-001", "products": [kw["product_type"]]}]}

def dealer_get_details(state, **kw):
    """PUBLIC. Gets dealer details."""
    if not kw.get("dealer_id"):
        return {"status": "error", "code": "MISSING_ID", "message": "Dealer ID required."}
    return {"status": "success", "dealer_id": kw["dealer_id"], "name": "Krishi Seeds", "license_status": "valid", "products": ["seeds", "pesticides"]}

def dealer_verify_license(state, **kw):
    """PUBLIC. Verifies dealer license."""
    if not kw.get("dealer_id"):
        return {"status": "error", "code": "MISSING_ID", "message": "Dealer ID required."}
    return {"status": "success", "dealer_id": kw["dealer_id"], "license_status": "valid", "expiry_date": "2025-12-31"}

def dealer_check_inventory(state, **kw):
    """PUBLIC. Checks product availability at dealer."""
    if not kw.get("dealer_id") or not kw.get("product_type"):
        return {"status": "error", "code": "MISSING_PARAMS", "message": "Dealer ID and product_type required."}
    return {"status": "success", "dealer_id": kw["dealer_id"], "product_type": kw["product_type"], "inventory_status": "available"}

def dealer_compare_options(state, **kw):
    """PUBLIC. Compares multiple dealers."""
    if not kw.get("location") or not kw.get("product_type"):
        return {"status": "error", "code": "MISSING_PARAMS", "message": "Location and product_type required."}
    return {"status": "success", "comparisons": [{"dealer_id": "DLR-001", "rating": 4.5, "inventory": "available"}, {"dealer_id": "DLR-002", "rating": 4.0, "inventory": "limited"}]}

def dealer_resolve_location_ambiguity(state, **kw):
    """PUBLIC. Resolves ambiguous locations."""
    if not kw.get("location"):
        return {"status": "error", "code": "MISSING_LOCATION", "message": "Location required."}
    return {"status": "success", "matches": [{"location": f"{kw['location']}, District A"}, {"location": f"{kw['location']}, District B"}]}

def dealer_resolve_duplicate_entries(state, **kw):
    """PUBLIC. Identifies duplicate dealer entries."""
    if not kw.get("location"):
        return {"status": "error", "code": "MISSING_LOCATION", "message": "Location required."}
    return {"status": "success", "duplicates": []}

def dealer_get_nearest(state, **kw):
    """PUBLIC. Returns nearest dealers."""
    if not kw.get("location"):
        return {"status": "error", "code": "MISSING_LOCATION", "message": "Location required."}
    return {"status": "success", "dealers": [{"dealer_id": "DLR-001", "distance_km": 3.2}]}

def dealer_get_recommendations(state, **kw):
    """Authenticated. Personalized dealer recommendations."""
    _val_session(kw.get("session_token"))
    return {"status": "success", "recommendations": [{"dealer_id": "DLR-001", "match_score": 0.95}]}

def dealer_save_preference(state, **kw):
    """Authenticated. Saves preferred dealer."""
    _val_session(kw.get("session_token"))
    state["preferred_dealer"] = kw.get("dealer_id")
    return {"status": "success", "dealer_id": kw.get("dealer_id"), "saved": True}

def dealer_raise_grievance(state, **kw):
    """Authenticated. Raises dealer grievance."""
    _val_session(kw.get("session_token"))
    cats = ("fake_dealer", "expired_license", "wrong_information", "product_not_available", "safety_violation")
    cat = kw.get("grievance_category")
    if cat not in cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {cats}")
    if not kw.get("description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("DEALER-GRV-")
    state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}

def dealer_track_grievance_status(state, **kw):
    """Authenticated. Tracks dealer grievance."""
    _val_session(kw.get("session_token"))
    gid = kw.get("grievance_id")
    if not gid:
        return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending"}


STUBS = {
    "dealer_search_by_location": dealer_search_by_location,
    "dealer_filter_by_product": dealer_filter_by_product,
    "dealer_get_details": dealer_get_details,
    "dealer_verify_license": dealer_verify_license,
    "dealer_check_inventory": dealer_check_inventory,
    "dealer_compare_options": dealer_compare_options,
    "dealer_resolve_location_ambiguity": dealer_resolve_location_ambiguity,
    "dealer_resolve_duplicate_entries": dealer_resolve_duplicate_entries,
    "dealer_get_nearest": dealer_get_nearest,
    "dealer_get_recommendations": dealer_get_recommendations,
    "dealer_save_preference": dealer_save_preference,
    "dealer_raise_grievance": dealer_raise_grievance,
    "dealer_track_grievance_status": dealer_track_grievance_status,
}
