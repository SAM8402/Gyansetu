import asyncio, sys, time 
sys.stdout.reconfigure(line_buffering=True) 
from app.ai.pipeline import create_initial_state, build_pipeline 
s = create_initial_state() 
s["job_id"] = "test" 
s["file_path"] = "test_upload.txt" 
s["config"] = {"subject": "ml", "topic": "ml"} 
p = build_pipeline() 
async def run(): 
    t0 = time.time() 
    try: 
        async for step in p.astream(s, {"recursion_limit": 50}): 
            node = list(step.keys())[0] 
            elapsed = time.time() - t0 
            print(f"[{elapsed:.0f}s] node={node}", flush=True) 
    except asyncio.TimeoutError: 
        print(f"TIMEOUT after {time.time()-t0:.0f}s", flush=True) 
print("starting astream...", flush=True) 
asyncio.run(run()) 
print("done", flush=True)
