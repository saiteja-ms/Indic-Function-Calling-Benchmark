import os

base_data_dir = r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\indic_fcb\data\Agriculture_farmers"
base_prompt_dir = r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\indic_fcb\prompts"

mappings = {
    "PM-KISAN (income support)": "pmkisan",
    "PM-KUSUM Solar Pump (energy subsidy)": "pmkusum",
    "PMFBY Crop Insurance (risk cover)": "pmfby",
    "Soil Health Card (soil info)": "soilhealth",
    "Crop Advisory (ATMA)": "atma",
    "Kisan Suvidha Weather (real-time)": "kisansuvidha",
    "Meghdoot Damini (alerts)": "meghdoot",
    "Soil Health Card Portal (test results)": "soilportal",
    "Agri Marketing (buy-sell) (FPO Trade)": "agrimarket",
    "AgriStack farmer registry (land records)": "agristack",
    "eNAM mandi (commodity prices)": "enam",
    "MSP procurement (govt. purchase)": "msp",
    "Kisan Call Centre (grievance)": "kcc",
    "PMFBY loss claim (crop damage)": "pmfbyloss",
    "SDRF-NDRF relief claim (flood-drought)": "sdrf",
    "iFMS fertilizer subsidy (DBT)": "ifms",
    "Pesticide-seed dealer (lookup)": "dealerlookup",
    "PM-PRANAM (urea rationalisation)": "pmpranam",
    "Animal Vaccination (health)": "animalvacc",
    "Dairy-Poultry subsidy (DEDS)": "deds",
    "e-Pashu Haat (buy-sell cattle)": "epashu",
    "NABARD livestock loan (credit)": "nabard",
    "Cold Storage-cluster (infrastructure)": "coldstorage",
    "Horticulture advisory (crop calendar)": "hortadvisory",
    "MIDH scheme application (subsidy)": "midh",
    "CHC Farm Machinery (rental portal)": "chc",
    "FMS custom hiring (booking)": "fms",
    "SMAM subsidy (tractor-harvester)": "smam",
    "JAL Jeevan Mission (rural water)": "jaljeevan",
    "PM-KUSUM grid power (solar)": "pmkusumgrid",
    "PMKSY irrigation (water scheme)": "pmksy"
}

template = """You are building an intent registry for a
function-calling benchmark.

READ:
  - tools.jsonl from the current usecase directory
  - personas.json from the current usecase directory

USECASE: {usecase}

TOOLS FILE:
{data_path}\\tools.jsonl

PERSONAS FILE:
{data_path}\\personas.json

STUB LOGIC FILE:
{data_path}\\stub_logic.py

STUB FILE:
{data_path}\\stubs.py

OUTPUT FILE:
{data_path}\\intents.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT IS AN INTENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

An intent is an abstract user goal, independent
of language and phrasing. Later, 3 scenario
variants (A, B, C) will be generated per intent.

An intent contains NO user prompt text —
only the abstract goal and metadata.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GUIDING PRINCIPLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Do NOT target a fixed number of intents.
Generate AS MANY intents as needed to achieve
COMPLETE COVERAGE of every category.

Complete coverage means:
  - every tool exercised in every meaningful way
  - every distractor trap covered
  - every domain-enforced chain covered
  - every commonly omitted parameter covered
  - every plausible-but-unavailable action covered
  - every adjacent-but-out-of-scope topic covered

More coverage is always better than less.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CATEGORY DEFINITIONS AND COVERAGE RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

── SIMPLE ──────────────────────────────

Definition:
  One tool call. All required parameters will
  be present in the user message.

How many to generate:
  - At minimum: one intent per tool
  - Additionally: one extra intent per tool
    that has meaningful parameter variations

Coverage complete when:
  Every tool has been exercised in every
  distinct parameter combination that a
  real farmer might use.

── MULTIPLE ────────────────────────────

Definition:
  Many tools available. Only ONE is correct.
  Distractor tools look tempting but are wrong.

How many to generate:
  One intent per distractor trap.
  Each trap must appear at least twice.

Coverage complete when:
  Every trap appears at least twice.

── PARALLEL ────────────────────────────

Definition:
  Two calls to the SAME tool with different
  parameters simultaneously.

Coverage complete when:
  Every tool with natural parallel use
  has at least one parallel intent.

── PARALLEL MULTIPLE ───────────────────

Definition:
  Two or more DIFFERENT tools called at the
  same time. Independent execution.

Coverage complete when:
  Every natural cross-tool pair covered.

── TASK IRRELEVANCE ────────────────────

Definition:
  Farmer query but NO tool applies.

Coverage complete when:
  All adjacent domains are covered.

── BASE (multi-turn) ───────────────────

Definition:
  Multi-step chain with domain constraints.

Coverage complete when:
  All real-world flows covered.

── MISS_PARAM (multi-turn) ─────────────

Definition:
  Missing required parameter.

Coverage complete when:
  All common missing parameters covered.

── MISS_FUNC (multi-turn) ──────────────

Definition:
  Unsupported action requested.

Coverage complete when:
  All realistic unsupported actions covered.

── LONG_CONTEXT (multi-turn) ───────────

Definition:
  Same as base but with long context.

Coverage complete when:
  Equal to base count.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT SCHEMA (EVERY INTENT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{
  "intent_id": "{short_usecase}_simple_001",
  "usecase": "{short_usecase}",
  "category": "simple",
  "abstract_goal": "...",
  "required_tools": ["..."],
  "chain_order_enforced": false,
  "domain_constraint": null,
  "suggested_persona": "PERSONA_A",
  "distractor_tools": [],
  "parallel_tools": [],
  "missing_param": null,
  "missing_func": null,
  "irrelevance_reason": null,
  "eval_notes": "..."
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SELF-VALIDATION BEFORE OUTPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ every tool in tools.jsonl appears in required_tools at least once  
✓ no invented tool names anywhere  
✓ all suggested_persona values exist in personas.json  
✓ chain_order_enforced true only for base and long_context  
✓ distractor_tools non-empty for multiple  
✓ parallel_tools non-empty for parallel and parallel_multiple  
✓ missing_param non-null for miss_param  
✓ missing_func non-null for miss_func  
✓ irrelevance_reason non-null for task_irrelevance  
✓ long_context count matches base count  

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Output ONLY a JSON array.
No markdown. No explanation.
No trailing commas. No missing fields.
No extra fields. No truncation.

SAVE TO:
{data_path}\\intents.json
"""

count = 0
clusters = os.listdir(base_data_dir)
for cluster in clusters:
    cluster_path = os.path.join(base_data_dir, cluster)
    if os.path.isdir(cluster_path):
        for usecase in os.listdir(cluster_path):
            if usecase in mappings:
                short_usecase = mappings[usecase]
                
                # Format paths
                data_path = os.path.join(base_data_dir, cluster, usecase)
                prompt_dir = os.path.join(base_prompt_dir, cluster, usecase)
                out_file = os.path.join(prompt_dir, "p5_intents.txt")
                
                if not os.path.exists(prompt_dir):
                    os.makedirs(prompt_dir, exist_ok=True)
                
                content = template.replace("{usecase}", usecase)
                content = content.replace("{short_usecase}", short_usecase)
                content = content.replace("{data_path}", data_path)
                
                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(content)
                count += 1
            else:
                print(f"Mapping not found for usecase: {usecase}")

print(f"Generated {count} p5_intents.txt files.")