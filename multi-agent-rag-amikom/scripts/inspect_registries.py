import json

# Conflict verifier
lines = [json.loads(l) for l in open('./data/immutable/chunk/Chunk_Corpus_RAG_AMIKOM_V1/chunk_conflict_verifier.jsonl', 'r', encoding='utf-8')]
print(f"Conflict records: {len(lines)}")
for l in lines:
    print(f"  {l['chunk_id']}: conflict_id={l.get('conflict_id','?')} response_mode={l.get('response_mode','?')}")

print()

# Blocked verifier
lines2 = [json.loads(l) for l in open('./data/immutable/chunk/Chunk_Corpus_RAG_AMIKOM_V1/chunk_blocked_verifier.jsonl', 'r', encoding='utf-8')]
print(f"Blocked records: {len(lines2)}")
for l in lines2:
    print(f"  {l['chunk_id']}: blocker_status={l.get('blocker_status','?')} response_mode={l.get('response_mode','?')}")

print()

# Control records stats
lines3 = [json.loads(l) for l in open('./data/immutable/chunk/Chunk_Corpus_RAG_AMIKOM_V1/chunk_control.jsonl', 'r', encoding='utf-8')]
print(f"Control records: {len(lines3)}")
ns_counts = {}
for l in lines3:
    ns = l.get('retrieval_namespace', '?')
    ns_counts[ns] = ns_counts.get(ns, 0) + 1
print(f"  Namespaces: {ns_counts}")
lifecycle_counts = {}
for l in lines3:
    lc = l.get('lifecycle_status', '?')
    lifecycle_counts[lc] = lifecycle_counts.get(lc, 0) + 1
print(f"  Lifecycle: {lifecycle_counts}")
