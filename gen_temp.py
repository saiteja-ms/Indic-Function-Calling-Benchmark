import json

intents = []
# 16 Simple intents
tools = [
    "pmkisan_generate_otp", "pmkisan_verify_otp", "pmkisan_register_farmer",
    "pmkisan_check_eligibility", "pmkisan_complete_ekyc", "pmkisan_get_beneficiary_status",
    "pmkisan_get_payment_history", "pmkisan_track_installment_status", "pmkisan_update_bank_details",
    "pmkisan_track_payment", "pmkisan_validate_land_records", "pmkisan_resolve_payment_failure",
    "pmkisan_get_installment_schedule", "pmkisan_resolve_eligibility_ambiguity",
    "pmkisan_raise_grievance", "pmkisan_track_grievance_status"
]

goals = [
    "Generate OTP for Aadhaar to start PM-KISAN authentication.",
    "Verify the OTP received to get the session token.",
    "Register a new farmer for PM-KISAN benefits.",
    "Check if the farmer is eligible for PM-KISAN.",
    "Complete OTP-based eKYC for the farmer.",
    "Retrieve the current beneficiary status.",
    "Get the complete payment history of past installments.",
    "Track the status of a specific installment.",
    "Update the bank account details linked to the farmer.",
    "Track the payment processing status.",
    "Validate the farmer's land ownership records.",
    "Initiate resolution for a failed PM-KISAN payment.",
    "Retrieve the installment schedule for the current year.",
    "Resolve ambiguous eligibility results.",
    "Raise a grievance related to PM-KISAN.",
    "Track the status of a previously raised grievance."
]

for i, tool in enumerate(tools):
    intents.append({
        "intent_id": f"pmkisan_simple_{i+1:03d}",
        "usecase": "pmkisan",
        "category": "simple",
        "abstract_goal": goals[i],
        "required_tools": [tool],
        "chain_order_enforced": False,
        "domain_constraint": None,
        "suggested_persona": "PERSONA_C",
        "distractor_tools": [],
        "parallel_tools": [],
        "missing_param": None,
        "missing_func": None,
        "irrelevance_reason": None,
        "eval_notes": "Basic simple tool call coverage."
    })

# Add Multiple
intents.extend([
    {
        "intent_id": "pmkisan_multiple_001",
        "usecase": "pmkisan",
        "category": "multiple",
        "abstract_goal": "Check beneficiary status (not payment history).",
        "required_tools": ["pmkisan_get_beneficiary_status"],
        "chain_order_enforced": False,
        "domain_constraint": None,
        "suggested_persona": "PERSONA_C",
        "distractor_tools": ["pmkisan_get_payment_history", "pmkisan_track_installment_status"],
        "parallel_tools": [],
        "missing_param": None,
        "missing_func": None,
        "irrelevance_reason": None,
        "eval_notes": "Distractor trap: get_payment_history looks tempting but goal is beneficiary status."
    },
    {
        "intent_id": "pmkisan_multiple_002",
        "usecase": "pmkisan",
        "category": "multiple",
        "abstract_goal": "Track status of a previously raised grievance.",
        "required_tools": ["pmkisan_track_grievance_status"],
        "chain_order_enforced": False,
        "domain_constraint": None,
        "suggested_persona": "PERSONA_F",
        "distractor_tools": ["pmkisan_raise_grievance"],
        "parallel_tools": [],
        "missing_param": None,
        "missing_func": None,
        "irrelevance_reason": None,
        "eval_notes": "Distractor trap: raise_grievance instead of track_grievance."
    }
])

# Add Parallel
intents.extend([
    {
        "intent_id": "pmkisan_parallel_001",
        "usecase": "pmkisan",
        "category": "parallel",
        "abstract_goal": "Track the status of both installment 1 and installment 2 at the same time.",
        "required_tools": ["pmkisan_track_installment_status"],
        "chain_order_enforced": False,
        "domain_constraint": None,
        "suggested_persona": "PERSONA_C",
        "distractor_tools": [],
        "parallel_tools": ["pmkisan_track_installment_status"],
        "missing_param": None,
        "missing_func": None,
        "irrelevance_reason": None,
        "eval_notes": "Parallel calls to the same tool for different installments."
    }
])

# Add Parallel Multiple
intents.extend([
    {
        "intent_id": "pmkisan_parallel_multiple_001",
        "usecase": "pmkisan",
        "category": "parallel_multiple",
        "abstract_goal": "Get beneficiary status and also get the installment schedule for the year.",
        "required_tools": ["pmkisan_get_beneficiary_status", "pmkisan_get_installment_schedule"],
        "chain_order_enforced": False,
        "domain_constraint": None,
        "suggested_persona": "PERSONA_C",
        "distractor_tools": [],
        "parallel_tools": ["pmkisan_get_beneficiary_status", "pmkisan_get_installment_schedule"],
        "missing_param": None,
        "missing_func": None,
        "irrelevance_reason": None,
        "eval_notes": "Parallel calls to two different tools."
    }
])

# Add Task Irrelevance
intents.extend([
    {
        "intent_id": "pmkisan_irrelevance_001",
        "usecase": "pmkisan",
        "category": "task_irrelevance",
        "abstract_goal": "Apply for a crop loan or tractor subsidy.",
        "required_tools": [],
        "chain_order_enforced": False,
        "domain_constraint": None,
        "suggested_persona": "PERSONA_C",
        "distractor_tools": ["pmkisan_register_farmer"],
        "parallel_tools": [],
        "missing_param": None,
        "missing_func": None,
        "irrelevance_reason": "Crop loan and tractor subsidies are out of scope for PM-KISAN.",
        "eval_notes": "Adjacent domain check."
    }
])

# Add Base
intents.extend([
    {
        "intent_id": "pmkisan_base_001",
        "usecase": "pmkisan",
        "category": "base",
        "abstract_goal": "Complete the full authentication flow (generate OTP, verify OTP) and then register the farmer.",
        "required_tools": ["pmkisan_generate_otp", "pmkisan_verify_otp", "pmkisan_register_farmer"],
        "chain_order_enforced": True,
        "domain_constraint": "Must authenticate before registering.",
        "suggested_persona": "PERSONA_A",
        "distractor_tools": [],
        "parallel_tools": [],
        "missing_param": None,
        "missing_func": None,
        "irrelevance_reason": None,
        "eval_notes": "Base flow: Auth -> Auth -> Register."
    }
])

# Add Miss Param
intents.extend([
    {
        "intent_id": "pmkisan_miss_param_001",
        "usecase": "pmkisan",
        "category": "miss_param",
        "abstract_goal": "Verify the OTP without providing the Aadhaar number.",
        "required_tools": ["pmkisan_verify_otp"],
        "chain_order_enforced": False,
        "domain_constraint": None,
        "suggested_persona": "PERSONA_A",
        "distractor_tools": [],
        "parallel_tools": [],
        "missing_param": "aadhaar_number",
        "missing_func": None,
        "irrelevance_reason": None,
        "eval_notes": "Missing required parameter Aadhaar."
    }
])

# Add Miss Func
intents.extend([
    {
        "intent_id": "pmkisan_miss_func_001",
        "usecase": "pmkisan",
        "category": "miss_func",
        "abstract_goal": "Delete the PM-KISAN account.",
        "required_tools": [],
        "chain_order_enforced": False,
        "domain_constraint": None,
        "suggested_persona": "PERSONA_C",
        "distractor_tools": ["pmkisan_raise_grievance"],
        "parallel_tools": [],
        "missing_param": None,
        "missing_func": "delete_account",
        "irrelevance_reason": None,
        "eval_notes": "Unsupported action."
    }
])

# Add Long Context
intents.extend([
    {
        "intent_id": "pmkisan_long_context_001",
        "usecase": "pmkisan",
        "category": "long_context",
        "abstract_goal": "Farmer explains long history of farming in their village, gives lots of irrelevant details about weather, and then asks to check their beneficiary status and payment history.",
        "required_tools": ["pmkisan_get_beneficiary_status", "pmkisan_get_payment_history"],
        "chain_order_enforced": True,
        "domain_constraint": "Sequential calls.",
        "suggested_persona": "PERSONA_E",
        "distractor_tools": [],
        "parallel_tools": [],
        "missing_param": None,
        "missing_func": None,
        "irrelevance_reason": None,
        "eval_notes": "Long context test."
    }
])

with open(r'C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\indic_fcb\data\Agriculture_farmers\1 Crop Schemes & Subsidies\PM-KISAN (income support)\intents.json', 'w', encoding='utf-8') as f:
    json.dump(intents, f, indent=2)