import json
import re

file_path = r'C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\data\simple\IFCB_v1_pmfby_simple.jsonl'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    text = text.replace('\r\n', '\n').strip()
    if text.startswith('['):
        data = json.loads(text)
    elif '}\n{' in text or '}\r\n{' in text:
        array_text = '[\n' + text.replace('}\n{', '},\n{') + '\n]'
        data = json.loads(array_text)
    else:
        data = [json.loads(line) for line in text.split('\n') if line.strip()]

    for item in data:
        for i, gt in enumerate(item.get('ground_truth', [])):
            if 'pmfby_calculate_premium' in gt:
                has_acres = 'land_area_acres' in gt
                has_district = 'district' in gt
                
                new_gt = gt
                prompt = item['question'][0][0]['content']
                
                if not has_acres:
                    if 'area_hectare' in new_gt:
                        new_gt = re.sub(r'area_hectare=[0-9.]+', "land_area_acres=5.0", new_gt)
                        prompt = re.sub(r'[0-9.]+\s*hectares?\s*of\s*land', "5 acres of land", prompt)
                    else:
                        new_gt = new_gt.replace(")", ", land_area_acres=5.0)")
                        prompt += " for 5 acres of land"
                
                if not has_district:
                    new_gt = new_gt.replace(")", ", district='Guntur')")
                    if 'district' not in prompt.lower():
                        prompt += " in Guntur district"

                item['ground_truth'][i] = new_gt
                item['question'][0][0]['content'] = prompt

    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
            
    print('SUCCESS')
except Exception as e:
    print('ERROR:', e)
