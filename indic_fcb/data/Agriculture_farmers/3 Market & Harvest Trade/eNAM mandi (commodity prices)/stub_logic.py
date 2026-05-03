import re, random, string


class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")


INITIAL_STATE = {
    "grievance_id": None,
    "session_token": None,
    "preferences_set": False,
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


def _val_session(v):
    if not isinstance(v, str) or not re.fullmatch(r"ENAM-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match ENAM-TKN-XXXXXXXX")

def _gen_id(pfx):
    return pfx + "".join(random.choices(string.digits, k=8))


def enam_get_mandi_prices(state, **kw):
    """PUBLIC. Current commodity prices at a mandi."""
    if not kw.get("commodity"):
        return {"status": "error", "code": "MISSING_COMMODITY", "message": "Commodity required."}
    return {"status": "success", "commodity": kw["commodity"], "location": kw.get("location"), "modal_price": 2200, "min_price": 2050, "max_price": 2400}


def enam_search_mandis(state, **kw):
    """PUBLIC. Search mandis by location."""
    if not kw.get("location"):
        return {"status": "error", "code": "INVALID_LOCATION", "message": "Location required."}
    return {"status": "success", "mandis": [{"mandi_id": "MND-001", "name": "Central Mandi", "commodities": ["paddy", "wheat"]}]}


def enam_compare_prices(state, **kw):
    """PUBLIC. Compare prices across mandis."""
    if not kw.get("commodity") or not kw.get("state"):
        return {"status": "error", "code": "MISSING_PARAMS", "message": "Commodity and state required."}
    return {"status": "success", "commodity": kw["commodity"], "comparisons": [{"mandi": "Mandi A", "modal_price": 2200}, {"mandi": "Mandi B", "modal_price": 2350}]}


def enam_get_price_trends(state, **kw):
    """PUBLIC. Historical price trends."""
    tr = kw.get("time_range")
    if tr not in ("today", "3_day", "7_day", "30_day"):
        raise ToolValidationError("time_range", tr, "Must be today/3_day/7_day/30_day")
    return {"status": "success", "commodity": kw.get("commodity"), "location": kw.get("location"), "trends": [{"date": "2024-07-01", "modal_price": 2200}]}


def enam_get_best_price(state, **kw):
    """PUBLIC. Best price for a commodity."""
    if not kw.get("commodity") or not kw.get("state"):
        return {"status": "error", "code": "MISSING_PARAMS", "message": "Commodity and state required."}
    return {"status": "success", "commodity": kw["commodity"], "best_mandi": "Central Mandi", "best_price": 2400}


def enam_get_arrival_data(state, **kw):
    """PUBLIC. Arrival quantities at a mandi."""
    return {"status": "success", "commodity": kw.get("commodity"), "location": kw.get("location"), "arrivals_quintal": 500, "demand_trend": "increasing"}


def enam_get_mandi_details(state, **kw):
    """PUBLIC. Mandi details."""
    if not kw.get("mandi_id"):
        return {"status": "error", "code": "MISSING_ID", "message": "Mandi ID required."}
    return {"status": "success", "mandi_id": kw["mandi_id"], "name": "Central Mandi", "address": "Main Road, District", "timings": "6AM-6PM"}


def enam_filter_prices(state, **kw):
    """PUBLIC. Filter prices by criteria."""
    return {"status": "success", "commodity": kw.get("commodity"), "location": kw.get("location"), "filtered_prices": [{"grade": kw.get("quality_grade", "FAQ"), "modal_price": 2200}]}


def enam_resolve_mandi_ambiguity(state, **kw):
    """PUBLIC. Resolve ambiguous mandi names."""
    if not kw.get("mandi_name"):
        return {"status": "error", "code": "MISSING_NAME", "message": "Mandi name required."}
    return {"status": "success", "matches": [{"mandi_id": "MND-001", "location": "District A"}, {"mandi_id": "MND-002", "location": "District B"}]}


def enam_set_preferences(state, **kw):
    """Authenticated. Set commodity/mandi preferences."""
    _val_session(kw.get("session_token"))
    state["preferences_set"] = True
    return {"status": "success", "commodities": kw.get("commodities"), "mandis": kw.get("mandis")}


def enam_raise_grievance(state, **kw):
    """Authenticated. Raise grievance."""
    _val_session(kw.get("session_token"))
    cats = ("incorrect_price", "missing_mandi_data", "delayed_update", "wrong_location", "commodity_not_found")
    cat = kw.get("grievance_category")
    if cat not in cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {cats}")
    if not kw.get("description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("ENAM-GRV-")
    state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}


def enam_track_grievance_status(state, **kw):
    """Authenticated. Track grievance."""
    _val_session(kw.get("session_token"))
    gid = kw.get("grievance_id")
    if not gid:
        return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending"}


STUBS = {
    "enam_get_mandi_prices": enam_get_mandi_prices,
    "enam_search_mandis": enam_search_mandis,
    "enam_compare_prices": enam_compare_prices,
    "enam_get_price_trends": enam_get_price_trends,
    "enam_get_best_price": enam_get_best_price,
    "enam_get_arrival_data": enam_get_arrival_data,
    "enam_get_mandi_details": enam_get_mandi_details,
    "enam_filter_prices": enam_filter_prices,
    "enam_resolve_mandi_ambiguity": enam_resolve_mandi_ambiguity,
    "enam_set_preferences": enam_set_preferences,
    "enam_raise_grievance": enam_raise_grievance,
    "enam_track_grievance_status": enam_track_grievance_status,
}
