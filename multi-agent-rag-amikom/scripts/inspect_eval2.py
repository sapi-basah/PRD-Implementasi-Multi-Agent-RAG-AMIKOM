import json

data = json.load(open('./data/immutable/evaluation/Baseline_RAG_Retrieval_Test_RAG_AMIKOM_V1/03_evaluation/baseline_rag_evaluation.json', 'r', encoding='utf-8'))
rows = data.get('rows', [])
# Print first row keys + full content
if rows:
    r = rows[0]
    print("Keys:", list(r.keys()))
    print("\nFull row 0:")
    for k, v in r.items():
        val = str(v)[:200] if isinstance(v, (str, list, dict)) else v
        print(f"  {k}: {val}")
