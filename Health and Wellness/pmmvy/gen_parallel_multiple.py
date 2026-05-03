import json
import random

with open(r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\Health and Wellness\pmmvy\tools\pmmvy_tools.json", "r", encoding="utf-8") as f:
    tools = json.load(f)

tool_dict = {t["name"]: t for t in tools}

def get_random_tools(exclude_names, count=2):
    pool = [t for name, t in tool_dict.items() if name not in exclude_names]
    return random.sample(pool, count)

cases_def = [
    {
        "id": "IFCB_v1_pmmvy_parallel_multiple_001",
        "question": "I want to apply for my first child. I am a BPL ration card holder. Also, my friend applied recently with ID APP-PM-100, can you track her app status?",
        "correct_tools": ["pmmvy_check_eligibility", "pmmvy_track_application_status"],
        "gt": [
            "pmmvy_check_eligibility(eligibility_category='bpl_ration_card', child_order='first_child')",
            "pmmvy_track_application_status(application_id='APP-PM-100')"
        ],
        "rationale": "PM1: pmmvy_check_eligibility + pmmvy_track_application_status"
    },
    {
        "id": "IFCB_v1_pmmvy_parallel_multiple_002",
        "question": "Track the status of application APP-PM-101. While you do that, check if a 40 percent disabled woman qualifies for her second child girl.",
        "correct_tools": ["pmmvy_check_eligibility", "pmmvy_track_application_status"],
        "gt": [
            "pmmvy_track_application_status(application_id='APP-PM-101')",
            "pmmvy_check_eligibility(eligibility_category='disabled_40_percent', child_order='second_child_girl')"
        ],
        "rationale": "PM1: pmmvy_check_eligibility + pmmvy_track_application_status"
    },
    {
        "id": "IFCB_v1_pmmvy_parallel_multiple_003",
        "question": "Has my first installment been approved in the system, and has the money actually come into my PFMS account? My app ID is APP-PM-200.",
        "correct_tools": ["pmmvy_check_installment_status", "pmmvy_check_payment_status"],
        "gt": [
            "pmmvy_check_installment_status(application_id='APP-PM-200', installment_number='installment_1')",
            "pmmvy_check_payment_status(application_id='APP-PM-200', installment_number='installment_1')"
        ],
        "rationale": "PM2: pmmvy_check_installment_status + pmmvy_check_payment_status"
    },
    {
        "id": "IFCB_v1_pmmvy_parallel_multiple_004",
        "question": "Check both the system approval stage and the actual bank payment credit for installment 2 for APP-PM-201.",
        "correct_tools": ["pmmvy_check_installment_status", "pmmvy_check_payment_status"],
        "gt": [
            "pmmvy_check_installment_status(application_id='APP-PM-201', installment_number='installment_2')",
            "pmmvy_check_payment_status(application_id='APP-PM-201', installment_number='installment_2')"
        ],
        "rationale": "PM2: pmmvy_check_installment_status + pmmvy_check_payment_status"
    },
    {
        "id": "IFCB_v1_pmmvy_parallel_multiple_005",
        "question": "My app is APP-PM-300. Is my ANC marked complete? Also, has my second installment been approved?",
        "correct_tools": ["pmmvy_check_anc_status", "pmmvy_check_installment_status"],
        "gt": [
            "pmmvy_check_anc_status(application_id='APP-PM-300')",
            "pmmvy_check_installment_status(application_id='APP-PM-300', installment_number='installment_2')"
        ],
        "rationale": "PM3: pmmvy_check_anc_status + pmmvy_check_installment_status"
    },
    {
        "id": "IFCB_v1_pmmvy_parallel_multiple_006",
        "question": "Can you verify if installment 2 is approved and also confirm my ANC completion status for APP-PM-301?",
        "correct_tools": ["pmmvy_check_anc_status", "pmmvy_check_installment_status"],
        "gt": [
            "pmmvy_check_installment_status(application_id='APP-PM-301', installment_number='installment_2')",
            "pmmvy_check_anc_status(application_id='APP-PM-301')"
        ],
        "rationale": "PM3: pmmvy_check_anc_status + pmmvy_check_installment_status"
    },
    {
        "id": "IFCB_v1_pmmvy_parallel_multiple_007",
        "question": "I filed a complaint GRV-12345. Track its status. Also, check if my first installment money came to my bank yet for APP-PM-400.",
        "correct_tools": ["pmmvy_track_grievance_status", "pmmvy_check_payment_status"],
        "gt": [
            "pmmvy_track_grievance_status(grievance_id='GRV-12345')",
            "pmmvy_check_payment_status(application_id='APP-PM-400', installment_number='installment_1')"
        ],
        "rationale": "PM4: pmmvy_track_grievance_status + pmmvy_check_payment_status"
    },
    {
        "id": "IFCB_v1_pmmvy_parallel_multiple_008",
        "question": "My app APP-PM-401 has a grievance GRV-98765. Track the grievance and check if the second installment hit my bank account via PFMS.",
        "correct_tools": ["pmmvy_track_grievance_status", "pmmvy_check_payment_status"],
        "gt": [
            "pmmvy_track_grievance_status(grievance_id='GRV-98765')",
            "pmmvy_check_payment_status(application_id='APP-PM-401', installment_number='installment_2')"
        ],
        "rationale": "PM4: pmmvy_track_grievance_status + pmmvy_check_payment_status"
    },
    {
        "id": "IFCB_v1_pmmvy_parallel_multiple_009",
        "question": "Check if my overall application APP-PM-500 is approved and whether my ANC is marked as complete.",
        "correct_tools": ["pmmvy_track_application_status", "pmmvy_check_anc_status"],
        "gt": [
            "pmmvy_track_application_status(application_id='APP-PM-500')",
            "pmmvy_check_anc_status(application_id='APP-PM-500')"
        ],
        "rationale": "PM5: pmmvy_track_application_status + pmmvy_check_anc_status"
    },
    {
        "id": "IFCB_v1_pmmvy_parallel_multiple_010",
        "question": "Tell me the overall status of application APP-PM-501 and also check its ANC completion status.",
        "correct_tools": ["pmmvy_track_application_status", "pmmvy_check_anc_status"],
        "gt": [
            "pmmvy_track_application_status(application_id='APP-PM-501')",
            "pmmvy_check_anc_status(application_id='APP-PM-501')"
        ],
        "rationale": "PM5: pmmvy_track_application_status + pmmvy_check_anc_status"
    }
]

cases = []
for c in cases_def:
    funcs = [tool_dict[t] for t in c["correct_tools"]]
    funcs += get_random_tools(c["correct_tools"], 3)
    
    case = {
        "id": c["id"],
        "usecase": "pmmvy",
        "language": "en",
        "intent_type": "parallel_multiple",
        "question": [[{"role": "user", "content": c["question"]}]],
        "function": funcs,
        "ground_truth": c["gt"],
        "parallel_rationale": c["rationale"]
    }
    cases.append(case)

out_path = r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\Health and Wellness\pmmvy\data\single_turn\pmmvy_parallel_multiple.jsonl"
with open(out_path, "w", encoding="utf-8") as f:
    for case in cases:
        f.write(json.dumps(case) + "\n")
