import os
import json
import itertools
import random

base_data_dir = r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\indic_fcb\data\Agriculture_farmers"
base_prompt_dir = r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\indic_fcb\prompts"

# 1. Update the p5_intents.txt files to demand more intents.
# We'll just append instructions to the end or replace text in them.
for root, dirs, files in os.walk(base_prompt_dir):
    if "p5_intents.txt" in files:
        p_path = os.path.join(root, "p5_intents.txt")
        with open(p_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Make replacements to demand higher counts
        content = content.replace(
            "── PARALLEL MULTIPLE ───────────────────\n\nDefinition:",
            "── PARALLEL MULTIPLE ───────────────────\n\nHow many to generate:\n  At least 5 distinct parallel multiple intents.\n\nDefinition:"
        )
        content = content.replace(
            "── TASK IRRELEVANCE ────────────────────\n\nDefinition:",
            "── TASK IRRELEVANCE ────────────────────\n\nHow many to generate:\n  At least 5 distinct task irrelevance intents (e.g. cricket, medical, railway, irrelevant scheme).\n\nDefinition:"
        )
        content = content.replace(
            "── BASE (multi-turn) ───────────────────\n\nDefinition:",
            "── BASE (multi-turn) ───────────────────\n\nHow many to generate:\n  At least 5 distinct multi-turn flows (chains of 2 to 3 tools).\n\nDefinition:"
        )
        
        with open(p_path, "w", encoding="utf-8") as f:
            f.write(content)

# 2. Re-generate intents.json with 5x more entries for those categories.
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

count = 0
clusters = os.listdir(base_data_dir)
for cluster in clusters:
    cluster_path = os.path.join(base_data_dir, cluster)
    if os.path.isdir(cluster_path):
        for usecase in os.listdir(cluster_path):
            if usecase in mappings:
                short_usecase = mappings[usecase]
                usecase_path = os.path.join(cluster_path, usecase)
                
                tools_file = os.path.join(usecase_path, "tools.jsonl")
                personas_file = os.path.join(usecase_path, "personas.json")
                out_file = os.path.join(usecase_path, "intents.json")
                
                if not os.path.exists(tools_file) or not os.path.exists(personas_file):
                    continue
                
                tools = []
                with open(tools_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                tools.append(json.loads(line))
                            except:
                                pass
                                
                personas = []
                with open(personas_file, 'r', encoding='utf-8') as f:
                    try:
                        personas_data = json.loads(f.read())
                        personas = [p["persona_id"] for p in personas_data]
                    except:
                        pass
                
                if not tools or not personas:
                    continue
                    
                persona_a = personas[0]
                persona_b = personas[1] if len(personas) > 1 else persona_a
                
                intents = []
                
                # 1. Simple
                for i, tool in enumerate(tools):
                    tool_name = tool.get("name", "")
                    desc = tool.get("description", "Execute tool call.")
                    goal = desc.split(".")[0] + "."
                    
                    intents.append({
                        "intent_id": f"{short_usecase}_simple_{i+1:03d}",
                        "usecase": short_usecase,
                        "category": "simple",
                        "abstract_goal": goal,
                        "required_tools": [tool_name],
                        "chain_order_enforced": False,
                        "domain_constraint": None,
                        "suggested_persona": persona_a,
                        "distractor_tools": [],
                        "parallel_tools": [],
                        "missing_param": None,
                        "missing_func": None,
                        "irrelevance_reason": None,
                        "eval_notes": "Basic simple coverage."
                    })
                
                # 2. Multiple
                pairs = list(itertools.combinations(tools, 2))
                for i, pair in enumerate(pairs[:5]):
                    intents.append({
                        "intent_id": f"{short_usecase}_multiple_{i+1:03d}",
                        "usecase": short_usecase,
                        "category": "multiple",
                        "abstract_goal": f"Perform action: {pair[0].get('description', '').split('.')[0]}.",
                        "required_tools": [pair[0]["name"]],
                        "chain_order_enforced": False,
                        "domain_constraint": None,
                        "suggested_persona": random.choice(personas),
                        "distractor_tools": [pair[1]["name"]],
                        "parallel_tools": [],
                        "missing_param": None,
                        "missing_func": None,
                        "irrelevance_reason": None,
                        "eval_notes": "Distractor trap."
                    })
                
                # 3. Parallel
                for i, tool in enumerate(tools[:3]):
                    intents.append({
                        "intent_id": f"{short_usecase}_parallel_{i+1:03d}",
                        "usecase": short_usecase,
                        "category": "parallel",
                        "abstract_goal": f"Perform this action twice simultaneously for two different entities: {tool['name']}.",
                        "required_tools": [tool["name"]],
                        "chain_order_enforced": False,
                        "domain_constraint": None,
                        "suggested_persona": random.choice(personas),
                        "distractor_tools": [],
                        "parallel_tools": [tool["name"]],
                        "missing_param": None,
                        "missing_func": None,
                        "irrelevance_reason": None,
                        "eval_notes": "Parallel execution."
                    })
                
                # 4. Parallel Multiple (5 entries)
                pm_pairs = list(itertools.combinations(tools, 2))
                random.seed(len(tools))
                random.shuffle(pm_pairs)
                for i, pair in enumerate(pm_pairs[:5]):
                    intents.append({
                        "intent_id": f"{short_usecase}_parallel_multiple_{i+1:03d}",
                        "usecase": short_usecase,
                        "category": "parallel_multiple",
                        "abstract_goal": f"Perform these two different actions simultaneously: {pair[0]['name']} and {pair[1]['name']}.",
                        "required_tools": [pair[0]["name"], pair[1]["name"]],
                        "chain_order_enforced": False,
                        "domain_constraint": None,
                        "suggested_persona": random.choice(personas),
                        "distractor_tools": [],
                        "parallel_tools": [pair[0]["name"], pair[1]["name"]],
                        "missing_param": None,
                        "missing_func": None,
                        "irrelevance_reason": None,
                        "eval_notes": "Parallel multiple execution."
                    })
                
                # 5. Task Irrelevance (5 entries)
                irrelevance_goals = [
                    ("Apply for a generic unrelated commercial loan from a private bank.", "Out of scope loan request."),
                    ("Ask about the latest cricket match scores and player statistics.", "Completely unrelated general knowledge query."),
                    ("Request medical advice for a persistent fever and headache.", "Unrelated medical query."),
                    ("Attempt to book a railway ticket from Delhi to Mumbai.", "Unrelated booking request."),
                    ("Inquire about the weather forecast in New York.", "Out of scope international query.")
                ]
                for i, (goal, reason) in enumerate(irrelevance_goals):
                    intents.append({
                        "intent_id": f"{short_usecase}_irrelevance_{i+1:03d}",
                        "usecase": short_usecase,
                        "category": "task_irrelevance",
                        "abstract_goal": goal,
                        "required_tools": [],
                        "chain_order_enforced": False,
                        "domain_constraint": None,
                        "suggested_persona": random.choice(personas),
                        "distractor_tools": [tools[0]["name"], tools[-1]["name"]] if len(tools) > 1 else [],
                        "parallel_tools": [],
                        "missing_param": None,
                        "missing_func": None,
                        "irrelevance_reason": reason,
                        "eval_notes": "Irrelevance coverage."
                    })
                
                # 6. Base (Multi-turn) (5 entries)
                base_pairs = []
                if len(tools) >= 2:
                    base_pairs.append([tools[0]["name"], tools[1]["name"]])
                    base_pairs.append([tools[-2]["name"], tools[-1]["name"]])
                if len(tools) >= 3:
                    base_pairs.append([tools[0]["name"], tools[2]["name"]])
                    base_pairs.append([tools[0]["name"], tools[1]["name"], tools[2]["name"]])
                    base_pairs.append([tools[1]["name"], tools[2]["name"]])
                elif len(tools) == 2:
                    base_pairs.extend([[tools[0]["name"], tools[1]["name"]]] * 3)
                
                for i, b_tools in enumerate(base_pairs[:5]):
                    intents.append({
                        "intent_id": f"{short_usecase}_base_{i+1:03d}",
                        "usecase": short_usecase,
                        "category": "base",
                        "abstract_goal": f"Execute the action sequence sequentially: {', '.join(b_tools)}.",
                        "required_tools": b_tools,
                        "chain_order_enforced": True,
                        "domain_constraint": "Sequential requirement.",
                        "suggested_persona": random.choice(personas),
                        "distractor_tools": [],
                        "parallel_tools": [],
                        "missing_param": None,
                        "missing_func": None,
                        "irrelevance_reason": None,
                        "eval_notes": "Base multi-turn coverage."
                    })
                
                # 7. Miss Param (up to 3)
                param_tools = [t for t in tools if t.get("parameters", {}).get("required", [])]
                for i, target_tool in enumerate(param_tools[:3]):
                    missing_param_name = target_tool.get("parameters", {}).get("required", [])[0]
                    intents.append({
                        "intent_id": f"{short_usecase}_miss_param_{i+1:03d}",
                        "usecase": short_usecase,
                        "category": "miss_param",
                        "abstract_goal": f"Attempt to perform {target_tool['name']} but do not provide the necessary {missing_param_name}.",
                        "required_tools": [target_tool["name"]],
                        "chain_order_enforced": False,
                        "domain_constraint": None,
                        "suggested_persona": random.choice(personas),
                        "distractor_tools": [],
                        "parallel_tools": [],
                        "missing_param": missing_param_name,
                        "missing_func": None,
                        "irrelevance_reason": None,
                        "eval_notes": "Miss param coverage."
                    })
                
                # 8. Miss Func
                intents.append({
                    "intent_id": f"{short_usecase}_miss_func_001",
                    "usecase": short_usecase,
                    "category": "miss_func",
                    "abstract_goal": "Ask to delete the account or update core details not supported by the system.",
                    "required_tools": [],
                    "chain_order_enforced": False,
                    "domain_constraint": None,
                    "suggested_persona": random.choice(personas),
                    "distractor_tools": [tools[0]["name"]] if tools else [],
                    "parallel_tools": [],
                    "missing_param": None,
                    "missing_func": "delete_account",
                    "irrelevance_reason": None,
                    "eval_notes": "Miss func coverage."
                })
                
                # 9. Long Context (5 entries)
                for i, b_tools in enumerate(base_pairs[:5]):
                    intents.append({
                        "intent_id": f"{short_usecase}_long_context_{i+1:03d}",
                        "usecase": short_usecase,
                        "category": "long_context",
                        "abstract_goal": f"Farmer shares a very long story about their village, crop history, and weather patterns over the last 10 years, and amidst this long narrative, asks to execute the sequence: {', '.join(b_tools)}.",
                        "required_tools": b_tools,
                        "chain_order_enforced": True,
                        "domain_constraint": "Sequential requirement.",
                        "suggested_persona": random.choice(personas),
                        "distractor_tools": [],
                        "parallel_tools": [],
                        "missing_param": None,
                        "missing_func": None,
                        "irrelevance_reason": None,
                        "eval_notes": "Long context coverage."
                    })
                
                with open(out_file, 'w', encoding='utf-8') as f:
                    json.dump(intents, f, indent=2)
                
                count += 1

print(f"Successfully generated expanded intents.json for {count} usecases.")