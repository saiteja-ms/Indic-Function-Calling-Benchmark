import re, random, string

class ToolValidationError(Exception):
    def __init__(self, field, value, reason):
        self.field, self.value, self.reason = field, value, reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value!r})")

INITIAL_STATE = {"session_token": None, "crop_stage": None, "grievance_id": None}

class StubContext:
    def __init__(self, state): self.state, self.call_log = state.copy(), []
    def call(self, tool_name, **kwargs):
        self.call_log.append({"tool": tool_name, "args": kwargs})
        if tool_name not in STUBS: raise ValueError(f"Unknown tool: {tool_name}")
        return STUBS[tool_name](self.state, **kwargs)
    def get_call_log(self): return self.call_log.copy()
    def reset(self, state): self.state, self.call_log = state.copy(), []

def _val_session(v):
    if not isinstance(v, str) or not re.fullmatch(r"HORTI-TKN-[A-Za-z0-9]{8}", v): raise ToolValidationError("session_token", v, "Must match HORTI-TKN-XXXXXXXX")
def _gen_id(pfx): return pfx + "".join(random.choices(string.digits, k=8))

VALID_CROPS = ("mango", "banana", "tomato", "potato", "onion", "chilli", "grapes", "flowers")
VALID_STAGES = ("land_preparation", "sowing", "vegetative", "flowering", "fruiting", "harvesting")

def horti_get_crop_calendar(state, **kw):
    ct = kw.get("crop_type")
    if ct not in VALID_CROPS: raise ToolValidationError("crop_type", ct, f"Must be one of {VALID_CROPS}")
    return {"status": "success", "crop_type": ct, "location": kw.get("location"), "stages": [{"stage": s, "duration_days": 30} for s in VALID_STAGES]}

def horti_get_stage_advisory(state, **kw):
    return {"status": "success", "crop_type": kw.get("crop_type"), "crop_stage": kw.get("crop_stage"), "advisory": "Follow recommended practices for this stage."}

def horti_get_weather_adjusted_advisory(state, **kw):
    return {"status": "success", "crop_type": kw.get("crop_type"), "advisory": "Delay irrigation due to expected rainfall.", "weather_impact": "moderate"}

def horti_get_pest_advisory(state, **kw):
    return {"status": "success", "crop_type": kw.get("crop_type"), "crop_stage": kw.get("crop_stage"), "pests": [{"name": "Fruit Fly", "prevention": "Pheromone traps", "treatment": "Neem oil spray"}]}

def horti_get_nutrient_advisory(state, **kw):
    return {"status": "success", "crop_type": kw.get("crop_type"), "crop_stage": kw.get("crop_stage"), "nutrients": [{"type": "NPK", "dosage_kg_per_acre": 25, "timing": "Pre-sowing"}]}

def horti_track_crop_stage(state, **kw):
    _val_session(kw.get("session_token"))
    state["crop_stage"] = "vegetative"
    return {"status": "success", "crop_type": kw.get("crop_type"), "estimated_stage": "vegetative", "sowing_date": kw.get("sowing_date")}

def horti_get_seasonal_plan(state, **kw):
    return {"status": "success", "crop_type": kw.get("crop_type"), "season": kw.get("season_type"), "plan": [{"stage": "sowing", "week": 1}, {"stage": "harvesting", "week": 16}]}

def horti_resolve_crop_ambiguity(state, **kw):
    return {"status": "success", "matches": [{"crop_type": "tomato", "confidence": "high"}]}

def horti_resolve_location_ambiguity(state, **kw):
    return {"status": "success", "matches": [{"location": f"{kw.get('location')}, District A"}]}

def horti_get_next_stage_guidance(state, **kw):
    cs = kw.get("current_stage")
    if cs == "harvesting": return {"status": "error", "code": "NO_NEXT_STAGE", "message": "Harvesting is the final stage."}
    idx = VALID_STAGES.index(cs) if cs in VALID_STAGES else 0
    return {"status": "success", "current_stage": cs, "next_stage": VALID_STAGES[min(idx+1, len(VALID_STAGES)-1)], "guidance": "Prepare for next stage."}

def horti_update_crop_stage(state, **kw):
    _val_session(kw.get("session_token"))
    state["crop_stage"] = kw.get("new_stage")
    return {"status": "success", "crop_type": kw.get("crop_type"), "new_stage": kw.get("new_stage")}

def horti_get_region_specific_calendar(state, **kw):
    return {"status": "success", "crop_type": kw.get("crop_type"), "location": kw.get("location"), "calendar": "Region-optimized schedule."}

def horti_raise_grievance(state, **kw):
    _val_session(kw.get("session_token"))
    cats = ("incorrect_advisory", "outdated_information", "crop_mismatch", "weather_conflict", "missing_guidance")
    if kw.get("grievance_category") not in cats: raise ToolValidationError("grievance_category", kw.get("grievance_category"), f"Must be one of {cats}")
    if not kw.get("description"): return {"status": "error", "code": "EMPTY_DESCRIPTION", "message": "Description required."}
    gid = _gen_id("HORTI-GRV-"); state["grievance_id"] = gid
    return {"status": "success", "grievance_id": gid}

def horti_track_grievance_status(state, **kw):
    _val_session(kw.get("session_token"))
    return {"status": "success", "grievance_id": kw.get("grievance_id"), "resolution_status": "pending"}

STUBS = {
    "horti_get_crop_calendar": horti_get_crop_calendar, "horti_get_stage_advisory": horti_get_stage_advisory,
    "horti_get_weather_adjusted_advisory": horti_get_weather_adjusted_advisory, "horti_get_pest_advisory": horti_get_pest_advisory,
    "horti_get_nutrient_advisory": horti_get_nutrient_advisory, "horti_track_crop_stage": horti_track_crop_stage,
    "horti_get_seasonal_plan": horti_get_seasonal_plan, "horti_resolve_crop_ambiguity": horti_resolve_crop_ambiguity,
    "horti_resolve_location_ambiguity": horti_resolve_location_ambiguity, "horti_get_next_stage_guidance": horti_get_next_stage_guidance,
    "horti_update_crop_stage": horti_update_crop_stage, "horti_get_region_specific_calendar": horti_get_region_specific_calendar,
    "horti_raise_grievance": horti_raise_grievance, "horti_track_grievance_status": horti_track_grievance_status,
}
