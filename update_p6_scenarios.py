import os

base_dir = r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\indic_fcb\prompts"

old_schema = """  "evaluation": {
    "type": "ast_match",
    "requires_stub_execution": false,
    "stub_stateful": false
  }"""

new_schema = """  "evaluation": {
    "type": "execution",
    "requires_stub_execution": true,
    "stub_stateful": false
  }"""

old_field_rules = """requires_stub_execution:
  false → single-turn, ast_match only
  true  → multi-turn, stub must run to evaluate

stub_stateful:
  false → single-turn
  true  → multi-turn base and long_context
          where state changes between turns"""

new_field_rules = """requires_stub_execution:
  true  → always true for all categories (execution evaluation)

stub_stateful:
  false → single-turn, miss_param, miss_func
  true  → multi-turn base and long_context
          where state changes between turns"""

count = 0
for root, dirs, files in os.walk(base_dir):
    if "p6_scenarios.txt" in files:
        filepath = os.path.join(root, "p6_scenarios.txt")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        modified = False
        
        if old_schema in content:
            content = content.replace(old_schema, new_schema)
            modified = True
            
        if old_field_rules in content:
            content = content.replace(old_field_rules, new_field_rules)
            modified = True
            
        # Replace category-specific false values
        if "requires_stub_execution: false" in content:
            content = content.replace("requires_stub_execution: false", "requires_stub_execution: true")
            modified = True
            
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            count += 1

print(f"Updated {count} files.")
