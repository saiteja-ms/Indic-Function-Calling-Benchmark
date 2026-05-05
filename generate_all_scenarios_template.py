import os, json, random, re

base_data_dir = r'C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\indic_fcb\data\Agriculture_farmers'

sys_prompt = '''You are a helpful assistant for Indian farmers
using the UMANG government services app.
You have access to tools for the appropriate
service. Help farmers complete their government
service requests accurately.

Rules:
- When a required parameter is missing, ask
  for it clearly. Do not guess or hallucinate.
- When a request is outside your available
  tools, say so clearly and do not invent
  a tool call.
- Always call authentication tools first
  when a session_token is needed.
- Never reveal session tokens to the user.'''

def get_eval_mode(param_name, param_type):
    if param_name in ['session_token', 'application_id', 'grievance_id', 'request_id', 'complaint_id', 'transaction_reference', 'beneficiary_id']:
        return 'type_only'
    if 'name' in param_name.lower() or 'description' in param_name.lower() or 'issue' in param_name.lower() or 'reason' in param_name.lower():
        return 'substring'
    return 'exact'

def get_missing_params(state_values, required_params):
    for p in required_params:
        if p not in state_values:
            state_values[p] = f'dummy_{p}_{random.randint(1000,9999)}'
            if 'aadhaar' in p: state_values[p] = f'10002000{random.randint(1000,9999)}'
            if 'mobile' in p: state_values[p] = f'98765{random.randint(10000,99999)}'

def generate_conversation(intent, variant, tools_map, state_values):
    category = intent['category']
    req_tools = intent['required_tools']
    
    if category in ['simple', 'multiple', 'parallel', 'parallel_multiple']:
        params_needed = []
        for t in req_tools:
            if t in tools_map:
                reqs = tools_map[t].get('parameters', {}).get('required', [])
                params_needed.extend([r for r in reqs if r != 'session_token'])
        params_needed = list(set(params_needed))
        
        get_missing_params(state_values, params_needed)
        param_str = ', '.join([f'my {p} is {state_values[p]}' for p in params_needed])
        
        if variant == 'A':
            text = f'I want to perform the following action: {intent["abstract_goal"]}. {param_str}.'
        elif variant == 'B':
            text = f'Namaste, can you help me? {intent["abstract_goal"]} Here are my details: {param_str}.'
        else:
            text = f'Hello, I have been farming for years and faced many issues. Recently, I heard about this service. {intent["abstract_goal"]} For your information, {param_str}.'
            
        return [{'role': 'user', 'content': text}]
        
    elif category == 'task_irrelevance':
        return [{'role': 'user', 'content': intent['abstract_goal']}]
        
    elif category == 'miss_func':
        return [{'role': 'user', 'content': 'I want to delete my account and erase all my records from the government database.'}]
        
    elif category in ['base', 'long_context', 'miss_param']:
        conv = []
        if category == 'long_context' and variant == 'C':
            conv.append({'role': 'user', 'content': 'I am a farmer from a small village. We have been waiting for rain.'})
            conv.append({'role': 'assistant', 'content': 'I understand. How can I help you today?'})
            conv.append({'role': 'user', 'content': 'The crops are not doing well this year.'})
            conv.append({'role': 'assistant', 'content': 'I am sorry to hear that. What service do you need?'})
            
        # Multi-turn chain
        for idx, t in enumerate(req_tools):
            params_needed = [p for p in tools_map[t].get('parameters', {}).get('required', []) if p != 'session_token']
            get_missing_params(state_values, params_needed)
            
            if category == 'miss_param' and idx == 0 and intent.get('missing_param'):
                mp = intent['missing_param']
                param_str_miss = ', '.join([f'my {p} is {state_values[p]}' for p in params_needed if p != mp])
                conv.append({'role': 'user', 'content': f'Please help me with {t}. {param_str_miss}'})
                conv.append({'role': 'assistant', 'content': f'Please provide your {mp}.'})
                conv.append({'role': 'user', 'content': f'My {mp} is {state_values[mp]}.'})
            else:
                param_str = ', '.join([f'my {p} is {state_values[p]}' for p in params_needed])
                conv.append({'role': 'user', 'content': f'Now let us proceed with {t}. {param_str}'})
                if idx < len(req_tools) - 1:
                    conv.append({'role': 'assistant', 'content': 'I have completed that step. What next?'})
        return conv
    
    return [{'role': 'user', 'content': 'Help me.'}]

def generate_ground_truth(intent, tools_map, state_values):
    category = intent['category']
    req_tools = intent['required_tools']
    
    if category in ['simple', 'multiple']:
        tool_name = req_tools[0] if req_tools else ''
        args = {}
        eval_m = {}
        if tool_name in tools_map:
            for p in tools_map[tool_name].get('parameters', {}).get('required', []):
                args[p] = state_values.get(p, f'dummy_{p}')
                if p == 'session_token': args[p] = '<from_auth_step>'
                eval_m[p] = get_eval_mode(p, 'string')
        return {'calls': [{'tool': tool_name, 'args': args, 'eval_mode': eval_m}], 'call_order': 'any'}
        
    elif category in ['parallel', 'parallel_multiple']:
        calls = []
        for t in (intent.get('parallel_tools') or req_tools):
            args = {}
            eval_m = {}
            if t in tools_map:
                for p in tools_map[t].get('parameters', {}).get('required', []):
                    args[p] = state_values.get(p, f'dummy_{p}')
                    if p == 'session_token': args[p] = '<from_auth_step>'
                    eval_m[p] = get_eval_mode(p, 'string')
            calls.append({'tool': t, 'args': args, 'eval_mode': eval_m})
        return {'calls': calls, 'call_order': 'any'}
        
    elif category in ['task_irrelevance']:
        return {'calls': [], 'call_order': 'any'}
        
    elif category in ['base', 'long_context', 'miss_param', 'miss_func']:
        calls = []
        if category == 'miss_param':
            calls.append([]) # Missing param turn
        if category == 'miss_func':
            calls.append([]) # Missing func turn
            
        for t in req_tools:
            args = {}
            eval_m = {}
            if t in tools_map:
                for p in tools_map[t].get('parameters', {}).get('required', []):
                    args[p] = state_values.get(p, f'dummy_{p}')
                    if p == 'session_token': args[p] = '<from_auth_step>'
                    eval_m[p] = get_eval_mode(p, 'string')
            calls.append([{'tool': t, 'args': args, 'eval_mode': eval_m}])
        return {'calls': calls, 'call_order': 'sequential'}
        
    return {'calls': [], 'call_order': 'any'}

count = 0
for cluster in os.listdir(base_data_dir):
    cluster_path = os.path.join(base_data_dir, cluster)
    if os.path.isdir(cluster_path):
        for usecase in os.listdir(cluster_path):
            usecase_path = os.path.join(cluster_path, usecase)
            if not os.path.isdir(usecase_path): continue
            
            intents_file = os.path.join(usecase_path, 'intents.json')
            personas_file = os.path.join(usecase_path, 'personas.json')
            tools_file = os.path.join(usecase_path, 'tools.jsonl')
            
            if not (os.path.exists(intents_file) and os.path.exists(personas_file) and os.path.exists(tools_file)):
                continue
                
            with open(intents_file, 'r', encoding='utf-8') as f: intents = json.load(f)
            with open(personas_file, 'r', encoding='utf-8') as f: personas = json.load(f)
            
            tools_map = {}
            with open(tools_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        t = json.loads(line)
                        tools_map[t['name']] = t
                        
            out_dir = os.path.join(usecase_path, 'scenarios', 'en')
            os.makedirs(out_dir, exist_ok=True)
            
            for intent in intents:
                for variant in ['A', 'B', 'C']:
                    p_id = intent.get('suggested_persona', personas[0]['persona_id'])
                    persona = next((p for p in personas if p['persona_id'] == p_id), personas[0])
                    state = dict(persona.get('state_values', {}))
                    
                    scenario_id = f"{intent['intent_id']}_{p_id}_{variant}"
                    
                    func_array = []
                    tools_to_include = list(set(intent.get('required_tools', []) + intent.get('distractor_tools', []) + intent.get('parallel_tools', [])))
                    if not tools_to_include and tools_map:
                        tools_to_include = [list(tools_map.keys())[0]]
                    for t in tools_to_include:
                        if t in tools_map: func_array.append(tools_map[t])
                        
                    gt = generate_ground_truth(intent, tools_map, state)
                    conv = generate_conversation(intent, variant, tools_map, state)
                    
                    cat = intent['category']
                    req_stub = True
                    stub_state = (cat in ['base', 'long_context'])
                    
                    scenario = {
                        'scenario_id': scenario_id,
                        'intent_id': intent['intent_id'],
                        'persona_id': p_id,
                        'variant': variant,
                        'category': cat,
                        'language': 'en',
                        'system_prompt': sys_prompt,
                        'conversation': conv,
                        'function': func_array,
                        'ground_truth': {
                            'calls': gt['calls'],
                            'call_order': gt['call_order'],
                            'stub_persona': p_id
                        },
                        'evaluation': {
                            'type': 'execution',
                            'requires_stub_execution': req_stub,
                            'stub_stateful': stub_state
                        }
                    }
                    
                    out_f = os.path.join(out_dir, f"{scenario_id}.json")
                    with open(out_f, 'w', encoding='utf-8') as f:
                        json.dump(scenario, f, indent=2)
                    count += 1

print(f'Successfully generated {count} scenarios.')
