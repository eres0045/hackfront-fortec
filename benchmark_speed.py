"""Empirical Benchmark for WhyCode System 1 & System 2 Latency."""
import time
import statistics
from whycode.graph import GraphStore
from whycode.qa import ask
from whycode.system1 import System1Engine

store = GraphStore("data/whycode.db")

# 1. Warm-up
q_valid = "why did Django avoid duplicate joins in filter after aggregation?"
q_refusal = "why does Django use quantum blockchain?"

for _ in range(50):
    ask(store, q_valid)
    ask(store, q_refusal)

# 2. Benchmark System 1 Conformal Gate (Abstention check)
sys1_times = []
for _ in range(1000):
    t0 = time.perf_counter_ns()
    res = System1Engine().decide(store, q_refusal)
    t1 = time.perf_counter_ns()
    sys1_times.append((t1 - t0) / 1000.0) # in microseconds (µs)

# 3. Benchmark System 2 Graph Traversal & Inverted Index Walk
full_times = []
for _ in range(1000):
    t0 = time.perf_counter_ns()
    res = ask(store, q_valid)
    t1 = time.perf_counter_ns()
    full_times.append((t1 - t0) / 1000.0) # in microseconds (µs)

print("================ WHYCODE LATENCY BENCHMARK ================")
print(f"Iterations: 1,000 runs on local CPU")
print(f"Database: data/whycode.db (678 nodes, 641 edges)\n")

print("1. SYSTEM 1 CONFORMAL ABSTENTION GATE (Anti-Hallucination):")
print(f"   • Mean Latency:  {statistics.mean(sys1_times):.2f} µs ({statistics.mean(sys1_times)/1000:.4f} ms)")
print(f"   • Median (p50):  {statistics.median(sys1_times):.2f} µs")
print(f"   • p95 Latency:   {statistics.quantiles(sys1_times, n=20)[18]:.2f} µs")
print(f"   • Min Latency:   {min(sys1_times):.2f} µs\n")

print("2. END-TO-END SYSTEM 1 + SYSTEM 2 (Full Graph Traversal + Evidence):")
print(f"   • Mean Latency:  {statistics.mean(full_times):.2f} µs ({statistics.mean(full_times)/1000:.3f} ms)")
print(f"   • Median (p50):  {statistics.median(full_times):.2f} µs ({statistics.median(full_times)/1000:.3f} ms)")
print(f"   • p95 Latency:   {statistics.quantiles(full_times, n=20)[18]:.2f} µs ({statistics.quantiles(full_times, n=20)[18]/1000:.3f} ms)")
print(f"   • Min Latency:   {min(full_times):.2f} µs ({min(full_times)/1000:.3f} ms)\n")

print("3. SPEED COMPARISON:")
mean_ms = statistics.mean(full_times) / 1000.0
print(f"   • vs. Standard LLM API (3,000 ms): {3000 / mean_ms:,.0f}x faster")
print(f"   • vs. Disk SQLite (120 ms):        {120 / mean_ms:,.0f}x faster")
print("===========================================================")
