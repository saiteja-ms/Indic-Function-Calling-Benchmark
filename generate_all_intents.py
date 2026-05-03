import os
import json

base_data_dir = r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\indic_fcb\data\Agriculture_farmers"

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
                
                # Load tools
                tools = []
                with open(tools_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                tools.append(json.loads(line))
                            except:
                                pass
                                
                # Load personas
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
                if len(tools) >= 2:
                    intents.append({
                        "intent_id": f"{short_usecase}_multiple_001",
                        "usecase": short_usecase,
                        "category": "multiple",
                        "abstract_goal": tools[0].get("description", "Perform action.").split(".")[0] + ".",
                        "required_tools": [tools[0]["name"]],
                        "chain_order_enforced": False,
                        "domain_constraint": None,
                        "suggested_persona": persona_b,
                        "distractor_tools": [tools[1]["name"]],
                        "parallel_tools": [],
                        "missing_param": None,
                        "missing_func": None,
                        "irrelevance_reason": None,
                        "eval_notes": "Distractor trap."
                    })
                    if len(tools) >= 3:
                        intents.append({
                            "intent_id": f"{short_usecase}_multiple_002",
                            "usecase": short_usecase,
                            "category": "multiple",
                            "abstract_goal": tools[1].get("description", "Perform action.").split(".")[0] + ".",
                            "required_tools": [tools[1]["name"]],
                            "chain_order_enforced": False,
                            "domain_constraint": None,
                            "suggested_persona": persona_a,
                            "distractor_tools": [tools[2]["name"], tools[0]["name"]],
                            "parallel_tools": [],
                            "missing_param": None,
                            "missing_func": None,
                            "irrelevance_reason": None,
                            "eval_notes": "Distractor trap 2."
                        })
                
                # 3. Parallel
                if len(tools) >= 1:
                    intents.append({
                        "intent_id": f"{short_usecase}_parallel_001",
                        "usecase": short_usecase,
                        "category": "parallel",
                        "abstract_goal": "Perform this action twice simultaneously for two different entities.",
                        "required_tools": [tools[0]["name"]],
                        "chain_order_enforced": False,
                        "domain_constraint": None,
                        "suggested_persona": persona_a,
                        "distractor_tools": [],
                        "parallel_tools": [tools[0]["name"]],
                        "missing_param": None,
                        "missing_func": None,
                        "irrelevance_reason": None,
                        "eval_notes": "Parallel execution."
                    })
                
                # 4. Parallel Multiple
                if len(tools) >= 2:
                    intents.append({
                        "intent_id": f"{short_usecase}_parallel_multiple_001",
                        "usecase": short_usecase,
                        "category": "parallel_multiple",
                        "abstract_goal": "Perform these two different actions simultaneously.",
                        "required_tools": [tools[0]["name"], tools[1]["name"]],
                        "chain_order_enforced": False,
                        "domain_constraint": None,
                        "suggested_persona": persona_b,
                        "distractor_tools": [],
                        "parallel_tools": [tools[0]["name"], tools[1]["name"]],
                        "missing_param": None,
                        "missing_func": None,
                        "irrelevance_reason": None,
                        "eval_notes": "Parallel multiple execution."
                    })
                
                # 5. Task Irrelevance
                intents.append({
                    "intent_id": f"{short_usecase}_irrelevance_001",
                    "usecase": short_usecase,
                    "category": "task_irrelevance",
                    "abstract_goal": "Apply for a generic unrelated loan or scheme.",
                    "required_tools": [],
                    "chain_order_enforced": False,
                    "domain_constraint": None,
                    "suggested_persona": persona_a,
                    "distractor_tools": [tools[0]["name"]] if tools else [],
                    "parallel_tools": [],
                    "missing_param": None,
                    "missing_func": None,
                    "irrelevance_reason": "Out of scope request for this domain.",
                    "eval_notes": "Irrelevance coverage."
                })
                
                # 6. Base (Multi-turn)
                if len(tools) >= 2:
                    intents.append({
                        "intent_id": f"{short_usecase}_base_001",
                        "usecase": short_usecase,
                        "category": "base",
                        "abstract_goal": "Execute the first action, then follow up with the second action in a multi-turn sequence.",
                        "required_tools": [tools[0]["name"], tools[1]["name"]],
                        "chain_order_enforced": True,
                        "domain_constraint": "Sequential requirement.",
                        "suggested_persona": persona_a,
                        "distractor_tools": [],
                        "parallel_tools": [],
                        "missing_param": None,
                        "missing_func": None,
                        "irrelevance_reason": None,
                        "eval_notes": "Base multi-turn coverage."
                    })
                
                # 7. Miss Param
                if tools:
                    # Find a tool with required parameters
                    target_tool = tools[0]
                    missing_param_name = "user_id"
                    reqs = target_tool.get("parameters", {}).get("required", [])
                    if reqs:
                        missing_param_name = reqs[0]
                        
                    intents.append({
                        "intent_id": f"{short_usecase}_miss_param_001",
                        "usecase": short_usecase,
                        "category": "miss_param",
                        "abstract_goal": "Attempt to perform the action but do not provide the necessary details.",
                        "required_tools": [target_tool["name"]],
                        "chain_order_enforced": False,
                        "domain_constraint": None,
                        "suggested_persona": persona_a,
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
                    "suggested_persona": persona_a,
                    "distractor_tools": [tools[0]["name"]] if tools else [],
                    "parallel_tools": [],
                    "missing_param": None,
                    "missing_func": "delete_account",
                    "irrelevance_reason": None,
                    "eval_notes": "Miss func coverage."
                })
                
                # 9. Long Context
                if len(tools) >= 2:
                    intents.append({
                        "intent_id": f"{short_usecase}_long_context_001",
                        "usecase": short_usecase,
                        "category": "long_context",
                        "abstract_goal": "Farmer shares a very long story about their village and weather history, then asks to execute the first action, followed by the second action.",
                        "required_tools": [tools[0]["name"], tools[1]["name"]],
                        "chain_order_enforced": True,
                        "domain_constraint": "Sequential requirement.",
                        "suggested_persona": persona_b,
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

print(f"Successfully generated intents.json for {count} usecases.")