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
        "id": "pmmvy_parallel_001",
        "question": "My app PM-MH-100 is approved. Tell me the status of my first and second installments.",
        "correct_tool": "pmmvy_check_installment_status",
        "gt": [
            "pmmvy_check_installment_status(application_id='PM-MH-100', installment_number='installment_1')",
            "pmmvy_check_installment_status(application_id='PM-MH-100', installment_number='installment_2')"
        ],
        "rationale": "P1: pmmvy_check_installment_status for TWO different installment numbers"
    },
    {
        "id": "pmmvy_parallel_002",
        "question": "Please check the PMMVY system approval stages for my second and third installments. My ID is PM-RJ-200.",
        "correct_tool": "pmmvy_check_installment_status",
        "gt": [
            "pmmvy_check_installment_status(application_id='PM-RJ-200', installment_number='installment_2')",
            "pmmvy_check_installment_status(application_id='PM-RJ-200', installment_number='installment_3')"
        ],
        "rationale": "P1: pmmvy_check_installment_status for TWO different installment numbers"
    },
    {
        "id": "pmmvy_parallel_003",
        "question": "My sister and I both applied for PMMVY. Can you check the first installment status for my app PM-UP-300 and her app PM-UP-301?",
        "correct_tool": "pmmvy_check_installment_status",
        "gt": [
            "pmmvy_check_installment_status(application_id='PM-UP-300', installment_number='installment_1')",
            "pmmvy_check_installment_status(application_id='PM-UP-301', installment_number='installment_1')"
        ],
        "rationale": "P2: pmmvy_check_installment_status for TWO different application_ids"
    },
    {
        "id": "pmmvy_parallel_004",
        "question": "Check the second installment approval for my daughter's ID PM-KA-400 and my daughter-in-law's ID PM-KA-401.",
        "correct_tool": "pmmvy_check_installment_status",
        "gt": [
            "pmmvy_check_installment_status(application_id='PM-KA-400', installment_number='installment_2')",
            "pmmvy_check_installment_status(application_id='PM-KA-401', installment_number='installment_2')"
        ],
        "rationale": "P2: pmmvy_check_installment_status for TWO different application_ids"
    },
    {
        "id": "pmmvy_parallel_005",
        "question": "Has the PFMS bank money come for my first installment on app PM-AP-500, and also check if my friend's first installment money came for PM-AP-501?",
        "correct_tool": "pmmvy_check_payment_status",
        "gt": [
            "pmmvy_check_payment_status(application_id='PM-AP-500', installment_number='installment_1')",
            "pmmvy_check_payment_status(application_id='PM-AP-501', installment_number='installment_1')"
        ],
        "rationale": "P3: pmmvy_check_payment_status for TWO different application_ids"
    },
    {
        "id": "pmmvy_parallel_006",
        "question": "Please confirm the actual bank credit for the third installment for PM-TN-600 and PM-TN-601.",
        "correct_tool": "pmmvy_check_payment_status",
        "gt": [
            "pmmvy_check_payment_status(application_id='PM-TN-600', installment_number='installment_3')",
            "pmmvy_check_payment_status(application_id='PM-TN-601', installment_number='installment_3')"
        ],
        "rationale": "P3: pmmvy_check_payment_status for TWO different application_ids"
    },
    {
        "id": "pmmvy_parallel_007",
        "question": "I filed two complaints. One was GRV-111 and the other GRV-222. What are their statuses?",
        "correct_tool": "pmmvy_track_grievance_status",
        "gt": [
            "pmmvy_track_grievance_status(grievance_id='GRV-111')",
            "pmmvy_track_grievance_status(grievance_id='GRV-222')"
        ],
        "rationale": "P4: pmmvy_track_grievance_status for TWO different grievance_ids"
    },
    {
        "id": "pmmvy_parallel_008",
        "question": "My sister filed grievance GRV-333 and I filed GRV-444 regarding payment delays. Check both.",
        "correct_tool": "pmmvy_track_grievance_status",
        "gt": [
            "pmmvy_track_grievance_status(grievance_id='GRV-333')",
            "pmmvy_track_grievance_status(grievance_id='GRV-444')"
        ],
        "rationale": "P4: pmmvy_track_grievance_status for TWO different grievance_ids"
    },
    {
        "id": "pmmvy_parallel_009",
        "question": "I have a BPL ration card and my sister has a PMJAY card. Both of us are expecting our first child. Check if we are eligible for PMMVY.",
        "correct_tool": "pmmvy_check_eligibility",
        "gt": [
            "pmmvy_check_eligibility(eligibility_category='bpl_ration_card', child_order='first_child')",
            "pmmvy_check_eligibility(eligibility_category='pmjay_beneficiary', child_order='first_child')"
        ],
        "rationale": "P5: pmmvy_check_eligibility for TWO different women with different eligibility_category values"
    },
    {
        "id": "pmmvy_parallel_010",
        "question": "My neighbor is a 40 percent disabled woman expecting her first child. I belong to the SC category and am expecting my second child (a girl). Can you check eligibility for both of us?",
        "correct_tool": "pmmvy_check_eligibility",
        "gt": [
            "pmmvy_check_eligibility(eligibility_category='disabled_40_percent', child_order='first_child')",
            "pmmvy_check_eligibility(eligibility_category='sc_st', child_order='second_child_girl')"
        ],
        "rationale": "P5: pmmvy_check_eligibility for TWO different women with different eligibility_category values"
    }
]

cases = []
for c in cases_def:
    funcs = [tool_dict[c["correct_tool"]]]
    funcs += get_random_tools([c["correct_tool"]], 3)
    
    case = {
        "id": c["id"],
        "usecase": "pmmvy",
        "language": "en",
        "intent_type": "parallel",
        "question": [[{"role": "user", "content": c["question"]}]],
        "function": funcs,
        "ground_truth": c["gt"],
        "parallel_rationale": c["rationale"]
    }
    cases.append(case)

out_path = r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\Health and Wellness\pmmvy\data\single_turn\pmmvy_parallel.jsonl"
with open(out_path, "w", encoding="utf-8") as f:
    for case in cases:
        f.write(json.dumps(case) + "\n")
