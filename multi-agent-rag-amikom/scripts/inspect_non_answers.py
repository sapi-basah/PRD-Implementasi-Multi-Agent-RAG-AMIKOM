import json

data = json.load(open('./data/immutable/evaluation/Baseline_RAG_Retrieval_Test_RAG_AMIKOM_V1/03_evaluation/baseline_rag_evaluation.json', 'r', encoding='utf-8'))
packs = json.load(open('./data/immutable/evaluation/Baseline_RAG_Retrieval_Test_RAG_AMIKOM_V1/02_results/context_packs.json', 'r', encoding='utf-8'))
q_map = {p["evaluation_id"]: p["question"] for p in packs.get("packs", [])}

for r in data.get("rows", []):
    eid = r["evaluation_id"]
    mode = r["expected_response_mode"]
    if mode != "ANSWER":
        print(f"{eid} | Mode: {mode} | Q: {q_map.get(eid)}")
