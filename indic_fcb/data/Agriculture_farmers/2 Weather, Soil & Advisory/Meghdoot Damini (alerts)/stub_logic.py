import re, random, string


class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")


INITIAL_STATE = {
    "subscription_status": None,
    "location_preferences": [],
    "grievance_id": None,
    "session_token": None,
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

def _val_session(v):
    if not isinstance(v, str) or not re.fullmatch(r"MEGHDOOT-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match MEGHDOOT-TKN-XXXXXXXX")

def _gen_id(pfx):
    return pfx + "".join(random.choices(string.digits, k=8))


def damini_get_lightning_alert(state, **kw):
    """PUBLIC. Real-time lightning alerts."""
    loc = kw.get("location")
    if not loc:
        return {"status": "error", "code": "INVALID_LOCATION", "message": "Location required."}
    return {"status": "success", "location": loc, "alert_status": "active", "severity": "high", "proximity_km": 15}


def damini_get_safety_advisory(state, **kw):
    """PUBLIC. Safety recommendations during lightning."""
    loc = kw.get("location")
    if not loc:
        return {"status": "error", "code": "INVALID_LOCATION", "message": "Location required."}
    return {"status": "success", "location": loc, "recommendations": ["Seek indoor shelter immediately", "Avoid open fields", "Stay away from metal objects"]}


def damini_check_alert_validity(state, **kw):
    """PUBLIC. Checks if alert is still active."""
    aid = kw.get("alert_id")
    if not aid:
        return {"status": "error", "code": "INVALID_ALERT_ID", "message": "Alert ID required."}
    return {"status": "success", "alert_id": aid, "alert_status": "active"}


def meghdoot_get_weather_alert(state, **kw):
    """PUBLIC. Weather-based alerts."""
    loc = kw.get("location")
    if not loc:
        return {"status": "error", "code": "INVALID_LOCATION", "message": "Location required."}
    return {"status": "success", "location": loc, "alerts": [{"alert_type": "rainfall", "severity": "moderate", "valid_until": "2024-07-15T18:00:00"}]}


def meghdoot_get_agro_advisory(state, **kw):
    """PUBLIC. Crop+weather agro-advisory."""
    loc = kw.get("location")
    if not loc:
        return {"status": "error", "code": "INVALID_LOCATION", "message": "Location required."}
    return {"status": "success", "location": loc, "crop_type": kw.get("crop_type"), "advisory": "Delay sowing by 3 days due to heavy rainfall forecast."}


def meghdoot_get_alert_history(state, **kw):
    """PUBLIC. Historical alerts."""
    loc = kw.get("location")
    if not loc:
        return {"status": "error", "code": "INVALID_LOCATION", "message": "Location required."}
    tw = kw.get("time_window")
    if tw not in ("1_hour", "3_hour", "24_hour"):
        raise ToolValidationError("time_window", tw, "Must be 1_hour/3_hour/24_hour")
    return {"status": "success", "location": loc, "time_window": tw, "history": []}


def meghdoot_subscribe_alerts(state, **kw):
    """Authenticated. Subscribe to alerts."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    if state.get("subscription_status") == "subscribed":
        return {"status": "error", "code": "ALREADY_SUBSCRIBED", "message": "Already subscribed."}
    state["subscription_status"] = "subscribed"
    return {"status": "success", "subscription_status": "subscribed", "location": kw.get("location")}


def meghdoot_unsubscribe_alerts(state, **kw):
    """Authenticated. Unsubscribe."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    if state.get("subscription_status") != "subscribed":
        return {"status": "error", "code": "NOT_SUBSCRIBED", "message": "Not subscribed."}
    state["subscription_status"] = "unsubscribed"
    return {"status": "success", "subscription_status": "unsubscribed"}


def meghdoot_set_location_preferences(state, **kw):
    """Authenticated. Sets preferred locations."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    locs = kw.get("locations")
    if not locs or not isinstance(locs, list):
        raise ToolValidationError("locations", locs, "Must be a non-empty list")
    state["location_preferences"] = locs
    return {"status": "success", "locations": locs}


def meghdoot_resolve_alert_conflict(state, **kw):
    """PUBLIC. Resolves conflicting alerts."""
    loc = kw.get("location")
    if not loc:
        return {"status": "error", "code": "INVALID_LOCATION", "message": "Location required."}
    return {"status": "success", "location": loc, "prioritized_alerts": [{"alert_type": "rainfall", "priority": 1}]}


def meghdoot_raise_grievance(state, **kw):
    """Authenticated. Raises grievance."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("alert_not_received", "incorrect_alert", "delayed_alert", "location_mismatch", "notification_failure")
    cat = kw.get("grievance_category")
    if cat not in cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {cats}")
    if not kw.get("description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("MEGHDOOT-GRV-")
    state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}


def meghdoot_track_grievance_status(state, **kw):
    """Authenticated. Tracks grievance."""
    _val_session(kw.get("session_token"))
    gid = kw.get("grievance_id")
    if not gid:
        return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending"}


STUBS = {
    "damini_get_lightning_alert": damini_get_lightning_alert,
    "damini_get_safety_advisory": damini_get_safety_advisory,
    "damini_check_alert_validity": damini_check_alert_validity,
    "meghdoot_get_weather_alert": meghdoot_get_weather_alert,
    "meghdoot_get_agro_advisory": meghdoot_get_agro_advisory,
    "meghdoot_get_alert_history": meghdoot_get_alert_history,
    "meghdoot_subscribe_alerts": meghdoot_subscribe_alerts,
    "meghdoot_unsubscribe_alerts": meghdoot_unsubscribe_alerts,
    "meghdoot_set_location_preferences": meghdoot_set_location_preferences,
    "meghdoot_resolve_alert_conflict": meghdoot_resolve_alert_conflict,
    "meghdoot_raise_grievance": meghdoot_raise_grievance,
    "meghdoot_track_grievance_status": meghdoot_track_grievance_status,
}
