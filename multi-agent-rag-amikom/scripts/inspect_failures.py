import json

data = json.load(open('./evaluation_report.json', 'r', encoding='utf-8'))
for d in data["details"]:
    if not d["response_mode_correct"]:
        print(f"FAILED: {d['evaluation_id']} | Expected: {d['expected_response_mode']} | Applied: {d['response_mode_applied']} | Q: {d['question']}")
