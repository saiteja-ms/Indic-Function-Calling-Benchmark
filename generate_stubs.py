import os
import json
import string

base_dir = r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\indic_fcb\data\Agriculture_farmers"

def get_persona_name(index):
    # 0 -> A, 25 -> Z, 26 -> AA
    name = ""
    while index >= 0:
        name = chr(65 + (index % 26)) + name
        index = (index // 26) - 1
    return f"PERSONA_{name}"

def format_dict_as_python(d):
    items = []
    for k, v in d.items():
        if v is True:
            val_str = "True"
        elif v is False:
            val_str = "False"
        elif v is None:
            val_str = "None"
        elif isinstance(v, str):
            val_str = f'"{v}"'
        elif isinstance(v, (int, float)):
            val_str = str(v)
        elif isinstance(v, list):
            # rudimentary list formatting, assuming lists are simple
            val_str = repr(v)
        else:
            val_str = repr(v)
        items.append(f'"{k}": {val_str}')
    return "{" + ", ".join(items) + "}"

count = 0

for root, dirs, files in os.walk(base_dir):
    if "stub_logic.py" in files and "personas.json" in files:
        stub_path = os.path.join(root, "stub_logic.py")
        personas_path = os.path.join(root, "personas.json")
        out_path = os.path.join(root, "stubs.py")

        with open(stub_path, "r", encoding="utf-8") as f:
            stub_content = f.read()
            
        with open(personas_path, "r", encoding="utf-8") as f:
            personas = json.load(f)

        persona_vars = []
        all_personas_dict = []
        
        for i, persona in enumerate(personas):
            p_name = get_persona_name(i)
            state_val = persona["state_values"]
            py_dict_str = format_dict_as_python(state_val)
            persona_vars.append(f"{p_name} = {py_dict_str}")
            all_personas_dict.append(f'    "{p_name}": {p_name}')
            
        block = "\n# ── PERSONA STATES ──────────────────────────────\n"
        block += "# Each persona is a filled INITIAL_STATE instance.\n"
        block += "# Pass one of these to StubContext() at scenario start.\n\n"
        
        block += "\n".join(persona_vars) + "\n\n"
        
        block += "ALL_PERSONAS = {\n" + ",\n".join(all_personas_dict) + "\n}\n\n"
        
        block += '''def get_persona(persona_id: str) -> dict:
    """Return a fresh copy of the named persona state."""
    if persona_id not in ALL_PERSONAS:
        raise ValueError(
            f"Unknown persona '{persona_id}'. "
            f"Valid: {list(ALL_PERSONAS.keys())}")
    return ALL_PERSONAS[persona_id].copy()
'''
        
        # Insert before class StubContext:
        parts = stub_content.split("class StubContext:")
        if len(parts) == 2:
            new_content = parts[0] + block + "\n\nclass StubContext:" + parts[1]
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            count += 1
        else:
            print(f"Could not find 'class StubContext:' in {stub_path}")

print(f"Processed {count} files.")