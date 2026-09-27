import sys
import json
import hashlib
import numpy as np
import chromadb
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
SNAPSHOT_PATH = ROOT / "frozen" / "vector_db_20k_snapshot"

client = chromadb.PersistentClient(path=str(SNAPSHOT_PATH))
col = client.get_collection("thinking_traces")
total_count = col.count()

BATCH_SIZE = 5000
all_ids = []
all_docs = []
all_embeddings = []

for offset in range(0, total_count, BATCH_SIZE):
    batch = col.get(limit=BATCH_SIZE, offset=offset, include=["documents", "embeddings"])
    all_ids.extend(batch["ids"])
    all_docs.extend(batch["documents"])
    all_embeddings.extend(batch["embeddings"])

# Sort by ID to ensure deterministic ordering
paired = sorted(zip(all_ids, all_docs, all_embeddings), key=lambda x: x[0])
sorted_ids = [p[0] for p in paired]
sorted_docs = [p[1] for p in paired]
sorted_embeddings = [p[2] for p in paired]

# 1. SHA-256 of sorted IDs
sha_ids = hashlib.sha256("\n".join(sorted_ids).encode("utf-8")).hexdigest()

# 2. SHA-256 of concatenated documents
sha_docs = hashlib.sha256("".join(sorted_docs).encode("utf-8")).hexdigest()

# 3. SHA-256 of embeddings as float32 bytes
emb_array = np.array(sorted_embeddings, dtype=np.float32)
sha_embeddings = hashlib.sha256(emb_array.tobytes()).hexdigest()

result = {
    "count": total_count,
    "sha256_sorted_ids": sha_ids,
    "sha256_concat_docs": sha_docs,
    "sha256_embeddings_float32": sha_embeddings
}

print(json.dumps(result))
