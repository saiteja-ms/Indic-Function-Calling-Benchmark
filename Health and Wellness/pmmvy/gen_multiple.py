import json
import random

with open(r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\Health and Wellness\pmmvy\tools\pmmvy_tools.json", "r", encoding="utf-8") as f:
    tools = json.load(f)

tool_dict = {t["name"]: t for t in tools}

def get_random_tools(exclude_names, count=4):
    pool = [t for name, t in tool_dict.items() if name not in exclude_names]
    return random.sample(pool, count)

cases_def = [
    {
        "id": "pmmvy_multiple_001",
        "question": "Has the money reached my PFMS bank account for my first installment? My application is PM-MH-123.",
        "correct": "pmmvy_check_payment_status",
        "trap": "pmmvy_check_installment_status",
        "gt": "pmmvy_check_payment_status(application_id='PM-MH-123', installment_number='installment_1')",
        "trap_name": "Trap A"
    },
    {
        "id": "pmmvy_multiple_002",
        "question": "Is my 2nd installment approved by the PMMVY system yet? App PM-UP-456",
        "correct": "pmmvy_check_installment_status",
        "trap": "pmmvy_check_payment_status",
        "gt": "pmmvy_check_installment_status(application_id='PM-UP-456', installment_number='installment_2')",
        "trap_name": "Trap A"
    },
    {
        "id": "pmmvy_multiple_003",
        "question": "Did my third installment arrive in my actual bank account? App PM-BR-789",
        "correct": "pmmvy_check_payment_status",
        "trap": "pmmvy_check_installment_status",
        "gt": "pmmvy_check_payment_status(application_id='PM-BR-789', installment_number='installment_3')",
        "trap_name": "Trap A"
    },
    {
        "id": "pmmvy_multiple_004",
        "question": "I submitted my PMMVY form yesterday. What is the status of my registration PM-RJ-101?",
        "correct": "pmmvy_track_application_status",
        "trap": "pmmvy_check_installment_status",
        "gt": "pmmvy_track_application_status(application_id='PM-RJ-101')",
        "trap_name": "Trap B"
    },
    {
        "id": "pmmvy_multiple_005",
        "question": "My registration is done. I want to check if my 1st installment is released by the system for App PM-TN-202.",
        "correct": "pmmvy_check_installment_status",
        "trap": "pmmvy_track_application_status",
        "gt": "pmmvy_check_installment_status(application_id='PM-TN-202', installment_number='installment_1')",
        "trap_name": "Trap B"
    },
    {
        "id": "pmmvy_multiple_006",
        "question": "Can you tell me if my overall PMMVY application APP-AP-303 is approved or rejected?",
        "correct": "pmmvy_track_application_status",
        "trap": "pmmvy_check_installment_status",
        "gt": "pmmvy_track_application_status(application_id='APP-AP-303')",
        "trap_name": "Trap B"
    },
    {
        "id": "pmmvy_multiple_007",
        "question": "I want to complain about not getting installment 2, but please check if my ANC status is marked complete first. App PM-KA-404",
        "correct": "pmmvy_check_anc_status",
        "trap": "pmmvy_raise_grievance",
        "gt": "pmmvy_check_anc_status(application_id='PM-KA-404')",
        "trap_name": "Trap C"
    },
    {
        "id": "pmmvy_multiple_008",
        "question": "My hospital uploaded my ANC details yesterday. Has it updated in the system for PM-MP-505? I need to check before filing a delay complaint.",
        "correct": "pmmvy_check_anc_status",
        "trap": "pmmvy_raise_grievance",
        "gt": "pmmvy_check_anc_status(application_id='PM-MP-505')",
        "trap_name": "Trap C"
    },
    {
        "id": "pmmvy_multiple_009",
        "question": "I have a PMJAY card and this is my first pregnancy. Can you check if I qualify for PMMVY?",
        "correct": "pmmvy_check_eligibility",
        "trap": "pmmvy_register_beneficiary",
        "gt": "pmmvy_check_eligibility(eligibility_category='pmjay_beneficiary', child_order='first_child')",
        "trap_name": "Trap D"
    },
    {
        "id": "pmmvy_multiple_010",
        "question": "I already checked my eligibility and I qualify. Please register me for my first child. My token is tok123, Aadhaar 123456789012, name Sita, under SC category.",
        "correct": "pmmvy_register_beneficiary",
        "trap": "pmmvy_check_eligibility",
        "gt": "pmmvy_register_beneficiary(session_token='tok123', name='Sita', aadhaar_number='123456789012', eligibility_category='sc_st', child_order='first_child')",
        "trap_name": "Trap D"
    },
    {
        "id": "pmmvy_multiple_011",
        "question": "Does a 40 percent disabled woman get benefits for a second child girl under PMMVY 2.0?",
        "correct": "pmmvy_check_eligibility",
        "trap": "pmmvy_register_beneficiary",
        "gt": "pmmvy_check_eligibility(eligibility_category='disabled_40_percent', child_order='second_child_girl')",
        "trap_name": "Trap D"
    },
    {
        "id": "pmmvy_multiple_012",
        "question": "I changed my bank branch. My token is tok456, app PM-GJ-606. Please change my account to 1122334455 with IFSC HDFC0001.",
        "correct": "pmmvy_update_bank_details",
        "trap": "pmmvy_update_mobile_number",
        "gt": "pmmvy_update_bank_details(session_token='tok456', application_id='PM-GJ-606', new_bank_account_number='1122334455', new_ifsc_code='HDFC0001')",
        "trap_name": "Trap E"
    },
    {
        "id": "pmmvy_multiple_013",
        "question": "My old phone is lost. My app is PM-DL-707, session tok789. Can you update my number to 9876543210?",
        "correct": "pmmvy_update_mobile_number",
        "trap": "pmmvy_update_bank_details",
        "gt": "pmmvy_update_mobile_number(session_token='tok789', application_id='PM-DL-707', new_mobile_number='9876543210')",
        "trap_name": "Trap E"
    },
    {
        "id": "pmmvy_multiple_014",
        "question": "I have not received my money for 4 months even though my first installment is approved. File a payment delay complaint. Token tok321, App PM-HR-808.",
        "correct": "pmmvy_raise_grievance",
        "trap": "pmmvy_track_grievance_status",
        "gt": "pmmvy_raise_grievance(session_token='tok321', application_id='PM-HR-808', grievance_category='payment_delay', description='Money not received for 4 months')",
        "trap_name": "Trap F"
    },
    {
        "id": "pmmvy_multiple_015",
        "question": "I filed a complaint yesterday about my rejected registration. The grievance number is GRV-WB-909. What is its current status?",
        "correct": "pmmvy_track_grievance_status",
        "trap": "pmmvy_raise_grievance",
        "gt": "pmmvy_track_grievance_status(grievance_id='GRV-WB-909')",
        "trap_name": "Trap F"
    }
]

cases = []
for c in cases_def:
    funcs = [tool_dict[c["correct"]], tool_dict[c["trap"]]]
    funcs += get_random_tools([c["correct"], c["trap"]], 4)
    # Ensure stable sorting for reproducibility if needed, but random is fine.
    
    case = {
        "id": c["id"],
        "usecase": "pmmvy",
        "language": "en",
        "intent_type": "multiple",
        "question": [[{"role": "user", "content": c["question"]}]],
        "function": funcs,
        "ground_truth": [c["gt"]],
        "distractor_trap": c["trap_name"]
    }
    cases.append(case)

out_path = r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\Health and Wellness\pmmvy\data\single_turn\pmmvy_multiple.jsonl"
with open(out_path, "w", encoding="utf-8") as f:
    for case in cases:
        f.write(json.dumps(case) + "\n")
