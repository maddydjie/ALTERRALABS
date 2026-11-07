"""One cached call end to end. Run twice: second call must be instant (cache hit)."""
import time
from src.models import generate

for i in range(2):
    t = time.time()
    out = generate("List the drug allergies in: 'Allergies: PCN (rash). NKFA.' Answer as a JSON list.")
    print(f"call {i+1}: {time.time()-t:.1f}s -> {out.strip()[:200]}")
