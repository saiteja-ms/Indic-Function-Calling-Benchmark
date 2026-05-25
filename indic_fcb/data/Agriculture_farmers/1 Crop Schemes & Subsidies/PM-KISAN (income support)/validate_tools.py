import json
from pathlib import Path

path = Path(r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\indic_fcb\data\Agriculture_farmers\1 Crop Schemes & Subsidies\PM-KISAN (income support)\tools.jsonl")
lines = [l.strip() for l in path.read_text().split("\n") if l.strip()]

tools = []
errors = []

for i, line in enumerate(lines, 1):
    try:
        tool = json.loads(line)
        tools.append(tool)
    except json.JSONDecodeError as e:
        errors.append(f"Line {i}: invalid JSON — {e}")

print(f"Parsed {len(tools)} tools\n")

tool_names = {t["name"] for t in tools}

for t in tools:
    name = t.get("name", "MISSING")
    desc = t.get("description", "")
    props = t.get("parameters", {}).get("properties", {})
    required = t.get("parameters", {}).get("required", [])

    # no cross-references
    for other in tool_names - {name}:
        if other in desc:
            errors.append(f"{name}: references '{other}' in description")

    # eval mode annotations
    for pname, pspec in props.items():
        pdesc = pspec.get("description", "")
        if not any(tag in pdesc for tag in
                   ["[EXACT]", "[SUBSTRING]", "[TYPE_ONLY]"]):
            errors.append(f"{name}.{pname}: missing eval mode")

    # session_token rules
    has_session = "session_token" in props
    session_required = "session_token" in required
    if has_session and not session_required:
        errors.append(f"{name}: session_token present but not required")

# public vs auth counts
public = [t for t in tools
          if "session_token" not in
          t.get("parameters", {}).get("properties", {})]
auth   = [t for t in tools
          if "session_token" in
          t.get("parameters", {}).get("properties", {})]

print(f"Public tools  : {len(public)}")
print(f"Auth tools    : {len(auth)}")

if len(public) < 4:
    errors.append(f"Only {len(public)} public tools — need at least 4")
if len(auth) < 6:
    errors.append(f"Only {len(auth)} auth tools — need at least 6")

if errors:
    print(f"\n{len(errors)} errors:")
    for e in errors:
        print(f"  ✗ {e}")
else:
    print("\n✓ tools.jsonl valid — proceed to stub_logic.py")