import json

data = json.load(open('./data/immutable/evaluation/Baseline_RAG_Retrieval_Test_RAG_AMIKOM_V1/03_evaluation/baseline_rag_evaluation.json', 'r', encoding='utf-8'))
rows = data.get('rows', [])
print(f"Total rows: {len(rows)}")
for r in rows[:5]:
    print(f"  {r.get('evaluation_id','?')}: domain={r.get('expected_domain','?')} mode={r.get('expected_response_mode','?')} query={r.get('query','?')[:60]}")

print("\n--- All evaluation IDs ---")
for r in rows:
    eid = r.get('evaluation_id','?')
    domain = r.get('expected_domain','?')
    mode = r.get('expected_response_mode','?')
    print(f"  {eid}: domain={domain} mode={mode}")
