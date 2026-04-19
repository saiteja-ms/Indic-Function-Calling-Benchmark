import json

file_path = r'C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\data\multi_turn\IFCB_v1_pmfby_multi_turn.jsonl'
tools_path = r'C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\tools\pmfby_tools.json'

with open(tools_path, 'r', encoding='utf-8') as f:
    tools = json.load(f)

def get_tool(name):
    for t in tools:
        if t['name'] == name:
            return t
    return None

new_cases = [
    {
        'id': 'IFCB_v1_pmfby_multi_turn_006',
        'usecase': 'pmfby',
        'language': 'en',
        'intent_type': 'multi_turn',
        'question': [[{'role': 'user', 'content': 'My maize crop in Kharif season got destroyed by a cyclone on 2025-08-15. Before I submit a claim, please check if maize is covered. If it is, apply for insurance for 3.0 hectares under my name Ravi Kumar with Aadhaar 112233445566 as a new application, and then submit the claim.'}]],
        'function': [get_tool('pmfby_get_crop_coverage_details'), get_tool('pmfby_submit_application'), get_tool('pmfby_submit_claim')],
        'ground_truth': [
            "pmfby_get_crop_coverage_details(crop_name='maize', season='Kharif')",
            "pmfby_submit_application(farmer_name='Ravi Kumar', aadhaar_number='112233445566', crop_name='maize', season='Kharif', area_hectare=3.0, application_type='new')",
            "pmfby_submit_claim(application_id='<from_previous_step>', crop_loss_cause='cyclone', loss_date='2025-08-15', season='Kharif')"
        ],
        'chain_rationale': 'A farmer cannot submit a claim without an active policy. Coverage details must be checked to confirm the crop and loss cause are notified before an application and subsequent claim are submitted.'
    },
    {
        'id': 'IFCB_v1_pmfby_multi_turn_007',
        'usecase': 'pmfby',
        'language': 'en',
        'intent_type': 'multi_turn',
        'question': [[{'role': 'user', 'content': 'I submitted a claim with ID CLM778899 a long time ago. Please check its status, and if it is delayed, raise a complaint for claim delay stating that money not received yet.'}]],
        'function': [get_tool('pmfby_check_claim_status'), get_tool('pmfby_raise_grievance')],
        'ground_truth': [
            "pmfby_check_claim_status(claim_id='CLM778899')",
            "pmfby_raise_grievance(reference_id='CLM778899', issue_type='claim_delay', description='money not received yet')"
        ],
        'chain_rationale': 'A grievance about a claim only makes sense after confirming the claims current status. Raising a grievance blindly wastes the farmers effort.'
    },
    {
        'id': 'IFCB_v1_pmfby_multi_turn_008',
        'usecase': 'pmfby',
        'language': 'en',
        'intent_type': 'multi_turn',
        'question': [[{'role': 'user', 'content': 'I am thinking of insuring my mustard crop for this Rabi season. I have 1.5 hectares of land. First, calculate the premium I have to pay. Then, go ahead and submit a renewal application for me. My name is Amit Singh and Aadhaar is 998877665544.'}]],
        'function': [get_tool('pmfby_calculate_premium'), get_tool('pmfby_submit_application')],
        'ground_truth': [
            "pmfby_calculate_premium(crop_name='mustard', season='Rabi', area_hectare=1.5)",
            "pmfby_submit_application(farmer_name='Amit Singh', aadhaar_number='998877665544', crop_name='mustard', season='Rabi', area_hectare=1.5, application_type='renewal')"
        ],
        'chain_rationale': 'A farmer should always verify premium before committing to an application, especially since premium varies by district and crop.'
    },
    {
        'id': 'IFCB_v1_pmfby_multi_turn_009',
        'usecase': 'pmfby',
        'language': 'en',
        'intent_type': 'multi_turn',
        'question': [[{'role': 'user', 'content': 'There was an unseasonal rain on 2025-03-20 that ruined my gram crop in the Rabi season. I need to claim insurance but I am not enrolled yet. Please check the coverage details for gram, enroll me (Sita Devi, Aadhaar 445566778899) for 2.5 hectares as a new applicant, and file the crop loss claim.'}]],
        'function': [get_tool('pmfby_get_crop_coverage_details'), get_tool('pmfby_submit_application'), get_tool('pmfby_submit_claim')],
        'ground_truth': [
            "pmfby_get_crop_coverage_details(crop_name='gram', season='Rabi')",
            "pmfby_submit_application(farmer_name='Sita Devi', aadhaar_number='445566778899', crop_name='gram', season='Rabi', area_hectare=2.5, application_type='new')",
            "pmfby_submit_claim(application_id='<from_previous_step>', crop_loss_cause='unseasonal_rain', loss_date='2025-03-20', season='Rabi')"
        ],
        'chain_rationale': 'A farmer cannot submit a claim without an active policy. Coverage details must be checked to confirm the crop and loss cause are notified before an application and subsequent claim are submitted.'
    },
    {
        'id': 'IFCB_v1_pmfby_multi_turn_010',
        'usecase': 'pmfby',
        'language': 'en',
        'intent_type': 'multi_turn',
        'question': [[{'role': 'user', 'content': 'My claim was rejected. My claim id is CLM334455. Verify the status of my claim first, and then raise a grievance for claim rejection, with the description rejected without proper farm inspection.'}]],
        'function': [get_tool('pmfby_check_claim_status'), get_tool('pmfby_raise_grievance')],
        'ground_truth': [
            "pmfby_check_claim_status(claim_id='CLM334455')",
            "pmfby_raise_grievance(reference_id='CLM334455', issue_type='claim_rejection', description='rejected without proper farm inspection')"
        ],
        'chain_rationale': 'A grievance about a claim only makes sense after confirming the claims current status. Raising a grievance blindly wastes the farmers effort.'
    }
]

with open(file_path, 'a', encoding='utf-8') as f:
    for case in new_cases:
        f.write(json.dumps(case) + '\n')

print('Successfully appended 5 new test cases.')
