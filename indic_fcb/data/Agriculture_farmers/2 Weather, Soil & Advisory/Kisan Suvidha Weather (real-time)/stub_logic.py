import re, random, string


class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")


INITIAL_STATE = {
    "subscription_status": None,
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
    if not isinstance(v, str) or not re.fullmatch(r"KSW-TKN-[A-Za-z0-9]{8}", v):
        raise ToolValidationError("session_token", v, "Must match KSW-TKN-XXXXXXXX")

def _gen_id(pfx):
    return pfx + "".join(random.choices(string.digits, k=8))


def ksweather_get_current_weather(state, **kw):
    """PUBLIC. Returns current weather."""
    loc = kw.get("location")
    if not loc:
        return {"status": "error", "code": "INVALID_LOCATION", "message": "Location required."}
    return {"status": "success", "location": loc, "temperature_c": 32.5, "humidity_pct": 65, "rainfall_mm": 0.0, "wind_speed_kmh": 12.3, "pressure_hpa": 1013}


def ksweather_get_weather_forecast(state, **kw):
    """PUBLIC. Returns forecast."""
    loc = kw.get("location")
    if not loc:
        return {"status": "error", "code": "INVALID_LOCATION", "message": "Location required."}
    tr = kw.get("time_range")
    if tr not in ("today", "3_day", "7_day", "10_day"):
        raise ToolValidationError("time_range", tr, "Must be today/3_day/7_day/10_day")
    return {"status": "success", "location": loc, "time_range": tr, "forecast": [{"day": 1, "temp_max": 34, "temp_min": 24, "rainfall_mm": 5}]}


def ksweather_get_weather_alerts(state, **kw):
    """PUBLIC. Returns active alerts."""
    loc = kw.get("location")
    if not loc:
        return {"status": "error", "code": "INVALID_LOCATION", "message": "Location required."}
    return {"status": "success", "location": loc, "alerts": []}


def ksweather_get_location_weather(state, **kw):
    """PUBLIC. Comprehensive weather data."""
    loc = kw.get("location")
    if not loc:
        return {"status": "error", "code": "INVALID_LOCATION", "message": "Location required."}
    return {"status": "success", "location": loc, "current": {"temperature_c": 32, "humidity_pct": 65}, "outlook": "Partly cloudy"}


def ksweather_get_weather_parameters(state, **kw):
    """PUBLIC. Specific weather parameters."""
    loc = kw.get("location")
    if not loc:
        return {"status": "error", "code": "INVALID_LOCATION", "message": "Location required."}
    wp = kw.get("weather_parameter")
    if wp not in ("temperature", "rainfall", "humidity", "wind_speed", "pressure"):
        raise ToolValidationError("weather_parameter", wp, "Invalid parameter")
    return {"status": "success", "location": loc, "weather_parameter": wp, "data_status": "available", "value": 32.5}


def ksweather_get_historical_weather(state, **kw):
    """PUBLIC. Historical weather data."""
    loc = kw.get("location")
    if not loc:
        return {"status": "error", "code": "INVALID_LOCATION", "message": "Location required."}
    return {"status": "success", "location": loc, "start_date": kw.get("start_date"), "end_date": kw.get("end_date"), "data": [{"date": kw.get("start_date"), "temp_max": 35}]}


def ksweather_resolve_location_ambiguity(state, **kw):
    """PUBLIC. Resolves ambiguous locations."""
    loc = kw.get("location")
    if not loc:
        return {"status": "error", "code": "INVALID_LOCATION", "message": "Location required."}
    return {"status": "success", "matches": [{"location": f"{loc}, District A"}, {"location": f"{loc}, District B"}]}


def ksweather_get_weather_advisory(state, **kw):
    """PUBLIC. Weather-based farming advisory."""
    loc = kw.get("location")
    if not loc:
        return {"status": "error", "code": "INVALID_LOCATION", "message": "Location required."}
    return {"status": "success", "location": loc, "activity_type": kw.get("activity_type"), "advisory": "Conditions favorable for sowing."}


def ksweather_subscribe_alerts(state, **kw):
    """Authenticated. Subscribe to alerts."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    if state.get("subscription_status") == "subscribed":
        return {"status": "error", "code": "ALREADY_SUBSCRIBED", "message": "Already subscribed."}
    state["subscription_status"] = "subscribed"
    return {"status": "success", "subscription_status": "subscribed", "location": kw.get("location")}


def ksweather_unsubscribe_alerts(state, **kw):
    """Authenticated. Unsubscribe from alerts."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    if state.get("subscription_status") != "subscribed":
        return {"status": "error", "code": "NOT_SUBSCRIBED", "message": "Not subscribed."}
    state["subscription_status"] = "unsubscribed"
    return {"status": "success", "subscription_status": "unsubscribed"}


def ksweather_raise_grievance(state, **kw):
    """Authenticated. Raises grievance."""
    _val_session(kw.get("session_token"))
    _val_aadhaar(kw.get("aadhaar_number"))
    cats = ("incorrect_forecast", "missing_weather_data", "delayed_update", "wrong_location", "alert_not_received")
    cat = kw.get("grievance_category")
    if cat not in cats:
        raise ToolValidationError("grievance_category", cat, f"Must be one of {cats}")
    if not kw.get("description"):
        return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("KSW-GRV-")
    state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}


def ksweather_track_grievance_status(state, **kw):
    """Authenticated. Tracks grievance."""
    _val_session(kw.get("session_token"))
    gid = kw.get("grievance_id")
    if not gid:
        return {"status": "error", "code": "INVALID_ID", "message": "Grievance ID required."}
    return {"status": "success", "grievance_id": gid, "resolution_status": "pending"}


STUBS = {
    "ksweather_get_current_weather": ksweather_get_current_weather,
    "ksweather_get_weather_forecast": ksweather_get_weather_forecast,
    "ksweather_get_weather_alerts": ksweather_get_weather_alerts,
    "ksweather_get_location_weather": ksweather_get_location_weather,
    "ksweather_get_weather_parameters": ksweather_get_weather_parameters,
    "ksweather_get_historical_weather": ksweather_get_historical_weather,
    "ksweather_resolve_location_ambiguity": ksweather_resolve_location_ambiguity,
    "ksweather_get_weather_advisory": ksweather_get_weather_advisory,
    "ksweather_subscribe_alerts": ksweather_subscribe_alerts,
    "ksweather_unsubscribe_alerts": ksweather_unsubscribe_alerts,
    "ksweather_raise_grievance": ksweather_raise_grievance,
    "ksweather_track_grievance_status": ksweather_track_grievance_status,
}
