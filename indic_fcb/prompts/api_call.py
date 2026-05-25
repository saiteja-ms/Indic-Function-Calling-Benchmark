"""
api_call.py — Scenario generator for IFCB.
Works for any usecase by reading its usecase_config.json.
"""

import os
import json
import re
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ── Pick the usecase here ────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Uncomment the usecase you want to run:

# 1. PM-KISAN
# USECASE_FOLDER = PROJECT_ROOT / "indic_fcb/data/Agriculture_farmers/1 Crop Schemes & Subsidies/PM-KISAN (income support)"

# 2. PM-KUSUM
USECASE_FOLDER = PROJECT_ROOT / "indic_fcb/data/Agriculture_farmers/2 Weather, Soil & Advisory/Crop Advisory (ATMA)"

# 3. PMFBY
# USECASE_FOLDER = PROJECT_ROOT / "indic_fcb/data/Agriculture_farmers/1 Crop Schemes & Subsidies/PMFBY Crop Insurance (risk cover)"

# 4. Soil Health Card
# USECASE_FOLDER = PROJECT_ROOT / "indic_fcb/data/Agriculture_farmers/1 Crop Schemes & Subsidies/Soil Health Card (soil info)"

# 5. Crop Advisory (ATMA)
# USECASE_FOLDER = PROJECT_ROOT / "indic_fcb/data/Agriculture_farmers/2 Weather, Soil & Advisory/Crop Advisory (ATMA)"


# Template lives in the prompts root, shared across usecases
TEMPLATE_PATH = SCRIPT_DIR / "p6_scenarios_template.txt"

# ── Config ───────────────────────────────────────────

env_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=env_path)

TOOLS_PATH    = USECASE_FOLDER / "tools.jsonl"
INTENTS_PATH  = USECASE_FOLDER / "intents.json"
CONFIG_PATH   = USECASE_FOLDER / "usecase_config.json"
OUT_DIR       = USECASE_FOLDER / "scenarios" / "en"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# persona file might be persona.json (like in PM-KISAN) or personas.json (other usecases)
PERSONA_PATH = USECASE_FOLDER / "persona.json"
if not PERSONA_PATH.exists():
    PERSONA_PATH = USECASE_FOLDER / "personas.json"

RETRY_LIMIT   = 3
SLEEP_BETWEEN = 1

COMPLEX_CATEGORIES = {
    "base", "long_context", "long_ctx",
    "miss_param", "miss_func"
}

# ── Load ─────────────────────────────────────────────

tools_by_name = {}
for line in TOOLS_PATH.read_text(encoding="utf-8").strip().split("\n"):
    if line.strip():
        t = json.loads(line)
        tools_by_name[t["name"]] = t

personas = json.loads(PERSONA_PATH.read_text(encoding="utf-8"))
intents  = json.loads(INTENTS_PATH.read_text(encoding="utf-8"))
config   = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
template = TEMPLATE_PATH.read_text(encoding="utf-8")

archetype_lookup = {p["archetype_id"]: p for p in personas}

# ── Render usecase-specific prompt ───────────────────

base_prompt = template
for key, value in config.items():
    base_prompt = base_prompt.replace(
        "{" + key + "}", value
    )

USECASE_PREFIX = config["USECASE_PREFIX"]

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# ── Helpers ──────────────────────────────────────────

def clean_json(raw):
    s = raw.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s)
    return s.strip()


def already_done(intent_id, archetype_id):
    sid = f"{USECASE_PREFIX}_{intent_id}_{archetype_id}"
    return (OUT_DIR / f"{sid}.json").exists()


def save_scenario(scenario):
    sid = scenario.get("scenario_id")
    if not sid:
        raise ValueError("scenario missing scenario_id")
    out_path = OUT_DIR / f"{sid}.json"
    out_path.write_text(
        json.dumps(scenario, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    return out_path


def pick_model(intent):
    return "gemini-3.1-pro-preview"


def pick_thinking_level(intent):
    if intent.get("category") in COMPLEX_CATEGORIES:
        return "LOW"
    return "none"


def build_prompt(base, intent, archetype, tools_by_name):
    needed = set(
        intent.get("required_tools", []) +
        intent.get("distractor_tools", []) +
        intent.get("parallel_tools", [])
    )
    relevant = [
        tools_by_name[n] for n in needed if n in tools_by_name
    ]
    tools_block = "\n".join(
        json.dumps(t, ensure_ascii=False) for t in relevant
    )

    injection = f"""

INPUT FOR THIS SCENARIO

Generate EXACTLY ONE scenario JSON object for
the intent and archetype below using only the
tools listed.

INTENT:
{json.dumps(intent, indent=2, ensure_ascii=False)}

ARCHETYPE:
{json.dumps(archetype, indent=2, ensure_ascii=False)}

RELEVANT TOOLS:
{tools_block}

Output a single JSON object. No markdown.
No array wrapper. No explanation.
"""
    return base + "\n" + injection


def fix_scenario(scenario):
    """Deterministic post-processing.
    Same logic as PM-KISAN version."""
    turns = scenario.get("conversation", [])
    gt_turns = [t for t in turns if t["speaker"] == "ground_truth"]
    user_turns = [t for t in turns if t["speaker"] == "user"]

    user_turn_count = len({t["turn_index"] for t in user_turns})
    max_calls = max(
        (len(t.get("tool_calls", [])) for t in gt_turns),
        default=0
    )
    all_null = (
        len(gt_turns) > 0 and
        all(t.get("null_call", False) for t in gt_turns)
    )
    has_irrelevance = any(
        t.get("irrelevance_reason") for t in gt_turns
    )
    diff_tools = False
    for t in gt_turns:
        calls = t.get("tool_calls", [])
        if len(calls) > 1:
            names = {c.get("tool_name") for c in calls}
            if len(names) > 1:
                diff_tools = True

    if all_null and has_irrelevance:
        task_type = "irrelevance"
    elif diff_tools:
        task_type = "parallel_multiple"
    else:
        task_type = "simple"

    scenario["axes"] = {
        "conversation_length": (
            "multi_turn" if user_turn_count > 1 else "single_turn"
        ),
        "tool_calls_per_turn": (
            "multi_step" if max_calls > 1 else "single_step"
        ),
        "task_type": task_type
    }

    user_text = " ".join(
        t.get("message", "") for t in user_turns
    )
    id_markers = (
        "aadhaar", "mobile", "otp", "_id",
        "_number", "_code", "_token", "ifsc",
        "amount", "date"
    )
    for t in gt_turns:
        for call in t.get("tool_calls", []):
            params = call.get("parameters", {})
            for pname, pspec in list(params.items()):
                if not isinstance(pspec, dict):
                    is_free_text = any(m in pname.lower() for m in ("remarks", "description", "details", "notes"))
                    pspec = {
                        "value": pspec,
                        "eval_mode": "SUBSTRING" if is_free_text else "EXACT"
                    }
                    params[pname] = pspec
            for pname, pspec in params.items():
                if pspec.get("eval_mode") != "TYPE_ONLY":
                    continue
                val = pspec.get("value")
                if val is None:
                    continue
                if pname == "session_token":
                    continue
                if str(val) in user_text:
                    is_id = any(
                        m in pname.lower() for m in id_markers
                    )
                    pspec["eval_mode"] = (
                        "EXACT" if is_id else "SUBSTRING"
                    )

    init = scenario.setdefault("initial_state", {})
    init["authenticated"] = False
    init["session_token"] = None

    return scenario


def call_model(prompt, intent, retries=RETRY_LIMIT):
    model_name = pick_model(intent)
    thinking = pick_thinking_level(intent)
    cfg = dict(
        temperature=0.0,
        response_mime_type="application/json",
        max_output_tokens=8192
    )
    if thinking != "none":
        cfg["thinking_config"] = types.ThinkingConfig(
            thinking_level=thinking
        )
    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(**cfg)
            )
            data = json.loads(clean_json(response.text))
            if isinstance(data, list):
                if len(data) == 1:
                    data = data[0]
                else:
                    raise ValueError(
                        f"got {len(data)} scenarios, expected 1"
                    )
            return data, response.usage_metadata, model_name
        except Exception as e:
            print(f"    attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(4 * attempt)
            else:
                raise


# ── Main loop ────────────────────────────────────────

pairs = []
for intent in intents:
    iid = intent["intent_id"]
    for arc_id in intent.get("compatible_archetypes", []):
        if arc_id not in archetype_lookup:
            print(f"  WARN: {arc_id} not in persona.json")
            continue
        pairs.append((intent, archetype_lookup[arc_id]))

total = len(pairs)
success = 0
skipped = 0
failed = []
total_in = 0
total_out = 0
total_think = 0

print(f"Usecase     : {config['USECASE_DISPLAY_NAME']}")
print(f"Total pairs : {total}")
print(f"Output dir  : {OUT_DIR}\n")

for idx, (intent, archetype) in enumerate(pairs, 1):
    iid = intent["intent_id"]
    aid = archetype["archetype_id"]
    cat = intent.get("category", "?")
    label = f"[{idx}/{total}] {iid} x {aid} ({cat})"

    if already_done(iid, aid):
        print(f"  SKIP  {label}")
        skipped += 1
        continue

    print(f"  GEN   {label}")
    try:
        prompt = build_prompt(
            base_prompt, intent, archetype, tools_by_name
        )
        scenario, usage, model_used = call_model(prompt, intent)
        scenario = fix_scenario(scenario)
        out_path = save_scenario(scenario)
        success += 1

        i_tok = getattr(usage, "prompt_token_count", 0) or 0
        o_tok = getattr(usage, "candidates_token_count", 0) or 0
        t_tok = (
            getattr(usage, "thinking_token_count", None) or
            getattr(usage, "thoughts_token_count", 0) or 0
        )
        total_in += i_tok
        total_out += o_tok
        total_think += t_tok

        percent = (idx / total) * 100
        print(f"        -> saved {out_path.name}")
        print(f"        -> model {model_used}")
        print(f"        -> tokens in={i_tok} out={o_tok} "
              f"think={t_tok}")
        print(f"        -> progress {percent:.1f}%")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"        -> FAILED: {e}")
        failed.append(f"{iid} x {aid}: {e}")

    time.sleep(SLEEP_BETWEEN)

print(f"\n{'=' * 60}")
print(f"Total pairs   : {total}")
print(f"Generated     : {success}")
print(f"Skipped       : {skipped}")
print(f"Failed        : {len(failed)}")
print(f"\nTokens:")
print(f"  Input       : {total_in:,}")
print(f"  Output      : {total_out:,}")
print(f"  Thinking    : {total_think:,}")
print(f"  Grand total : {total_in + total_out + total_think:,}")

if failed:
    fail_log = OUT_DIR.parent / "failed_pairs.txt"
    fail_log.write_text("\n".join(failed), encoding="utf-8")
    print(f"\nFailed log: {fail_log}")