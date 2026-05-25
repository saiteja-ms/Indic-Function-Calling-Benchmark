import os
import json
import re
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ── Config ────────────────────────────────────────────────────────────────────

env_path = r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\.env"
load_dotenv(dotenv_path=env_path)

BASE = Path(r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\indic_fcb\data\Agriculture_farmers\1 Crop Schemes & Subsidies\PM-KUSUM Solar Pump (energy subsidy)")

TOOLS_PATH   = BASE / "tools.jsonl"
PERSONA_PATH = BASE / "personas.json"
INTENTS_PATH = BASE / "intents.json"
PROMPT_PATH  = Path(r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\indic_fcb\prompts\1 Crop Schemes & Subsidies\PM-KUSUM Solar Pump(enery subsidy)\p6_scenarios.txt")
OUT_DIR      = BASE / "scenarios" / "en"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RETRY_LIMIT   = 3
SLEEP_BETWEEN = 1

# Categories needing deeper reasoning use Pro;
# simpler ones use Flash to save cost.
COMPLEX_CATEGORIES = {
    "base", "long_context", "long_ctx",
    "miss_param", "miss_func"
}

# ── Load files ────────────────────────────────────────────────────────────────

# Parse tools.jsonl into a dict for selective injection
tools_by_name = {}
for line in TOOLS_PATH.read_text(encoding="utf-8").strip().split("\n"):
    if line.strip():
        t = json.loads(line)
        tools_by_name[t["name"]] = t

personas    = json.loads(PERSONA_PATH.read_text(encoding="utf-8"))
intents     = json.loads(INTENTS_PATH.read_text(encoding="utf-8"))
base_prompt = PROMPT_PATH.read_text(encoding="utf-8")

archetype_lookup = {p["archetype_id"]: p for p in personas}

# ── Gemini client ─────────────────────────────────────────────────────────────

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# ── Helpers ───────────────────────────────────────────────────────────────────

def clean_json(raw: str) -> str:
    """Strip markdown code fences if the model adds them."""
    s = raw.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s)
    return s.strip()


def already_done(intent_id: str, archetype_id: str) -> bool:
    sid = f"{intent_id}_{archetype_id}"
    return (OUT_DIR / f"{sid}.json").exists()


def save_scenario(scenario: dict) -> Path:
    sid = scenario.get("scenario_id")
    if not sid:
        raise ValueError("scenario missing scenario_id")
    out_path = OUT_DIR / f"{sid}.json"
    out_path.write_text(
        json.dumps(scenario, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    return out_path


def pick_model(intent: dict) -> str:
    """Use Gemini 3.1 Pro Preview for all runs."""
    return "gemini-3.1-pro-preview"


def pick_thinking_level(intent: dict) -> str:
    """Use HIGH thinking level for deep reasoning."""
    return "HIGH"


def build_prompt(
    base: str,
    intent: dict,
    archetype: dict,
    tools_by_name: dict
) -> str:
    """
    Inject ONLY this intent, this archetype, and the
    tools this intent actually references.
    """
    # collect tools referenced by this intent
    needed_tool_names = set(
        intent.get("required_tools", []) +
        intent.get("distractor_tools", []) +
        intent.get("parallel_tools", [])
    )
    relevant_tools = [
        tools_by_name[n]
        for n in needed_tool_names
        if n in tools_by_name
    ]
    tools_block = "\n".join(
        json.dumps(t, ensure_ascii=False)
        for t in relevant_tools
    )

    injection = f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INPUT FOR THIS SCENARIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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


# ── Post-processing: fix axes and eval_modes deterministically ────────────────

def fix_scenario(scenario: dict) -> dict:
    """
    Catch model mistakes that survive the prompt rules.
    Applied to every scenario before saving.

    Fixes:
      1. axes derived from the actual conversation
      2. TYPE_ONLY downgraded to EXACT/SUBSTRING when
         the value is visible in user messages
      3. authenticated forced to False in initial_state
      4. session_token forced to null in initial_state
    """
    turns = scenario.get("conversation", [])
    gt_turns = [
        t for t in turns if t["speaker"] == "ground_truth"
    ]
    user_turns = [
        t for t in turns if t["speaker"] == "user"
    ]

    # ── Fix 1: derive axes from conversation ───────────
    user_turn_count = len({t["turn_index"] for t in user_turns})

    max_calls_in_turn = max(
        (len(t.get("tool_calls", [])) for t in gt_turns),
        default=0
    )

    all_null = (
        len(gt_turns) > 0 and
        all(t.get("null_call", False) for t in gt_turns)
    )
    has_irrelevance = any(
        t.get("irrelevance_reason")
        for t in gt_turns
    )

    diff_tools_in_one_turn = False
    for t in gt_turns:
        calls = t.get("tool_calls", [])
        if len(calls) > 1:
            tool_names = {c.get("tool_name") for c in calls}
            if len(tool_names) > 1:
                diff_tools_in_one_turn = True

    if all_null and has_irrelevance:
        task_type = "irrelevance"
    elif diff_tools_in_one_turn:
        task_type = "parallel_multiple"
    else:
        task_type = "simple"

    scenario["axes"] = {
        "conversation_length": (
            "multi_turn" if user_turn_count > 1
            else "single_turn"
        ),
        "tool_calls_per_turn": (
            "multi_step" if max_calls_in_turn > 1
            else "single_step"
        ),
        "task_type": task_type
    }

    # ── Fix 2: TYPE_ONLY on visible values ─────────────
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
            for pname, pspec in call.get(
                "parameters", {}
            ).items():
                if pspec.get("eval_mode") != "TYPE_ONLY":
                    continue
                val = pspec.get("value")
                if val is None:
                    continue
                # session_token is legitimately TYPE_ONLY
                if pname == "session_token":
                    continue
                # if value appears in user text,
                # it can't be TYPE_ONLY
                if str(val) in user_text:
                    is_identifier = any(
                        m in pname.lower()
                        for m in id_markers
                    )
                    pspec["eval_mode"] = (
                        "EXACT" if is_identifier
                        else "SUBSTRING"
                    )

    # ── Fix 3: force initial_state defaults ────────────
    init = scenario.setdefault("initial_state", {})
    init["authenticated"] = False
    init["session_token"] = None

    return scenario


# ── Model call ────────────────────────────────────────────────────────────────

def call_model(
    prompt: str,
    intent: dict,
    retries: int = RETRY_LIMIT
) -> tuple:
    """
    Returns (scenario_dict, usage_metadata, model_name).
    Retries on parse or API errors.
    """
    model_name     = pick_model(intent)
    thinking_level = pick_thinking_level(intent)

    cfg_kwargs = dict(
        temperature=0.0,
        response_mime_type="application/json",
        max_output_tokens=8192
    )
    if thinking_level != "none":
        cfg_kwargs["thinking_config"] = types.ThinkingConfig(
            thinking_level=thinking_level
        )

    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(**cfg_kwargs)
            )
            cleaned = clean_json(response.text)
            data = json.loads(cleaned)

            # handle list with one item
            if isinstance(data, list):
                if len(data) == 1:
                    data = data[0]
                else:
                    raise ValueError(
                        f"got {len(data)} scenarios, expected 1"
                    )
            if not isinstance(data, dict):
                raise TypeError(
                    f"expected dict, got {type(data).__name__}"
                )

            return data, response.usage_metadata, model_name

        except Exception as e:
            print(f"    attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(4 * attempt)
            else:
                raise


# ── Pair building ─────────────────────────────────────────────────────────────

pairs = []
for intent in intents:
    intent_id   = intent["intent_id"]
    compatible  = intent.get("compatible_archetypes", [])
    for arc_id in compatible:
        if arc_id not in archetype_lookup:
            print(
                f"  WARNING: {arc_id} not in "
                f"persona.json — skipping"
            )
            continue
        pairs.append((intent, archetype_lookup[arc_id]))

total       = len(pairs)
success     = 0
skipped     = 0
failed      = []
total_in    = 0
total_out   = 0
total_think = 0

print(f"Total intent × archetype pairs : {total}")
print(f"Output directory               : {OUT_DIR}\n")

# ── Main loop ─────────────────────────────────────────────────────────────────

for idx, (intent, archetype) in enumerate(pairs, 1):
    intent_id    = intent["intent_id"]
    archetype_id = archetype["archetype_id"]
    category     = intent.get("category", "?")
    label = (
        f"[{idx}/{total}] {intent_id} "
        f"× {archetype_id} ({category})"
    )

    if already_done(intent_id, archetype_id):
        print(f"  SKIP  {label}")
        skipped += 1
        continue

    print(f"  GEN   {label}")

    try:
        prompt = build_prompt(
            base_prompt, intent, archetype, tools_by_name
        )
        scenario, usage, model_used = call_model(
            prompt, intent
        )

        # post-process to guarantee correctness
        scenario = fix_scenario(scenario)

        out_path = save_scenario(scenario)
        success += 1

        # token tracking
        i_tok = getattr(usage, "prompt_token_count", 0) or 0
        o_tok = getattr(usage, "candidates_token_count", 0) or 0
        t_tok = (
            getattr(usage, "thinking_token_count", None) or
            getattr(usage, "thoughts_token_count", 0) or 0
        )
        total_in    += i_tok
        total_out   += o_tok
        total_think += t_tok

        percent = (idx / total) * 100
        print(f"        → saved {out_path.name}")
        print(f"        → model {model_used}")
        print(
            f"        → tokens "
            f"in={i_tok} out={o_tok} think={t_tok}"
        )
        print(f"        → progress {percent:.1f}%")

    except Exception as e:
        print(f"        → FAILED: {e}")
        failed.append(f"{intent_id} × {archetype_id}: {e}")

    time.sleep(SLEEP_BETWEEN)

# ── Summary ───────────────────────────────────────────────────────────────────

print(f"\n{'=' * 60}")
print(f"Total pairs   : {total}")
print(f"Generated     : {success}")
print(f"Skipped       : {skipped} (already existed)")
print(f"Failed        : {len(failed)}")
print(f"\nCumulative tokens:")
print(f"  Input       : {total_in:,}")
print(f"  Output      : {total_out:,}")
print(f"  Thinking    : {total_think:,}")
print(f"  Grand total : {total_in + total_out + total_think:,}")

if failed:
    print("\nFailed pairs:")
    for f in failed:
        print(f"  ✗ {f}")
    fail_log = OUT_DIR.parent / "failed_pairs.txt"
    fail_log.write_text("\n".join(failed), encoding="utf-8")
    print(f"\nFailed pairs logged to: {fail_log}")