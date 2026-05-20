import anthropic
from pathlib import Path

client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var

prompt = Path("prompts/p1_tools.txt").read_text()
prompt = prompt.replace("[USECASE]", "PM-KISAN")
# ... any other substitutions ...

response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=16000,
    messages=[{"role": "user", "content": prompt}]
)

output = response.content[0].text
Path("data/farmers/pm_kisan/tools.jsonl").write_text(output)