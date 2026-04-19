import json

file_path = r'C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\data\parallel\IFCB_v1_pmfby_parallel.jsonl'
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
        'id': 'IFCB_v1_pmfby_parallel_006',
        'usecase': 'pmfby',
        'language': 'en',
        'intent_type': 'parallel',
        'question': [[{'role': 'user', 'content': 'Can you check the premium for both wheat and mustard this Rabi season for my 3.5 hectares of land?'}]],
        'function': [get_tool('pmfby_calculate_premium')],
        'ground_truth': [
            "pmfby_calculate_premium(crop_name='wheat', season='Rabi', area_hectare=3.5)",
            "pmfby_calculate_premium(crop_name='mustard', season='Rabi', area_hectare=3.5)"
        ],
        'parallel_rationale': 'Both premium calculations are independent lookups for different crops. Neither result is needed to compute the other.'
    },
    {
        'id': 'IFCB_v1_pmfby_parallel_007',
        'usecase': 'pmfby',
        'language': 'en',
        'intent_type': 'parallel',
        'question': [[{'role': 'user', 'content': 'I need to know the application status for APP998877 and also the claim status for CLM112233.'}]],
        'function': [get_tool('pmfby_check_application_status'), get_tool('pmfby_check_claim_status')],
        'ground_truth': [
            "pmfby_check_application_status(application_id='APP998877')",
            "pmfby_check_claim_status(claim_id='CLM112233')"
        ],
        'parallel_rationale': 'Application status and claim status are independent lookups for different IDs. Neither output is required by the other.'
    },
    {
        'id': 'IFCB_v1_pmfby_parallel_008',
        'usecase': 'pmfby',
        'language': 'en',
        'intent_type': 'parallel',
        'question': [[{'role': 'user', 'content': 'Please check the coverage details for maize in Kharif season and also find the nearest enrollment center in Kurnool district of Andhra Pradesh.'}]],
        'function': [get_tool('pmfby_get_crop_coverage_details'), get_tool('pmfby_find_enrollment_center')],
        'ground_truth': [
            "pmfby_get_crop_coverage_details(crop_name='maize', season='Kharif')",
            "pmfby_find_enrollment_center(district='Kurnool', state='Andhra Pradesh')"
        ],
        'parallel_rationale': 'Coverage lookup and enrollment center search are unrelated read-only operations. One provides insurance coverage info while the other provides geographical info.'
    },
    {
        'id': 'IFCB_v1_pmfby_parallel_009',
        'usecase': 'pmfby',
        'language': 'en',
        'intent_type': 'parallel',
        'question': [[{'role': 'user', 'content': 'Can you check my grievance status with reference GRV445566 and also check my claim status with ID CLM998877?'}]],
        'function': [get_tool('pmfby_track_grievance_status'), get_tool('pmfby_check_claim_status')],
        'ground_truth': [
            "pmfby_track_grievance_status(grievance_id='GRV445566')",
            "pmfby_check_claim_status(claim_id='CLM998877')"
        ],
        'parallel_rationale': 'Tracking grievance and checking claim status are completely independent status lookups for different entities.'
    },
    {
        'id': 'IFCB_v1_pmfby_parallel_010',
        'usecase': 'pmfby',
        'language': 'en',
        'intent_type': 'parallel',
        'question': [[{'role': 'user', 'content': 'I want to know the premium for both gram and barley crops in Rabi season for 5 hectares of land.'}]],
        'function': [get_tool('pmfby_calculate_premium')],
        'ground_truth': [
            "pmfby_calculate_premium(crop_name='gram', season='Rabi', area_hectare=5.0)",
            "pmfby_calculate_premium(crop_name='barley', season='Rabi', area_hectare=5.0)"
        ],
        'parallel_rationale': 'Both premium calculations are for different crops in the same season. Neither result is needed to compute the other — they are fully independent computations.'
    }
]

with open(file_path, 'a', encoding='utf-8') as f:
    for case in new_cases:
        f.write(json.dumps(case) + '\n')
