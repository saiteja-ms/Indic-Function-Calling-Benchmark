import json
from pathlib import Path

path = Path("data/farmers/pm_kisan/tools.jsonl")
lines = path.read_text().strip().split("\n")

tools = []
for i, line in enumerate(lines, 1):
    line = line.strip()
    if not line:
        continue
    try:
        tool = json.loads(line)
        tools.append(tool)
    except json.JSONDecodeError as e:
        print(f"  ✗ line {i}: invalid JSON — {e}")

print(f"\nParsed {len(tools)} tools.\n")

# rule checks
tool_names = {t["name"] for t in tools}
errors = []

for t in tools:
    name = t["name"]
    desc = t.get("description", "")

    # rule: no tool can name another tool
    for other in tool_names - {name}:
        if other in desc:
            errors.append(
                f"  ✗ {name} references {other} "
                f"in description")

    # rule: every parameter ends with eval mode marker
    props = t["parameters"].get("properties", {})
    for pname, pspec in props.items():
        pdesc = pspec.get("description", "")
        if not any(
            tag in pdesc
            for tag in ["[EXACT]", "[SUBSTRING]", "[TYPE_ONLY]"]
        ):
            errors.append(
                f"  ✗ {name}.{pname} missing eval mode")

# rule: minimum public/auth counts
public_tools = [
    t for t in tools
    if "session_token" not in t["parameters"]["properties"]
]
auth_tools = [
    t for t in tools
    if "session_token" in t["parameters"]["properties"]
]

if len(public_tools) < 4:
    errors.append(
        f"  ✗ only {len(public_tools)} public tools, need ≥ 4")
if len(auth_tools) < 6:
    errors.append(
        f"  ✗ only {len(auth_tools)} auth tools, need ≥ 6")

if errors:
    print(f"{len(errors)} issues:")
    for e in errors:
        print(e)
else:
    print("✓ all checks passed")