import asyncio, sys, time 
sys.stdout.reconfigure(line_buffering=True) 
from app.ai.pipeline import create_initial_state, build_pipeline  
s = create_initial_state()  
s["job_id"] = "test"  
s["file_path"] = "test_upload.txt"  
s["config"] = {"subject": "ml", "topic": "ml"}  
pipeline = build_pipeline()  
async def run():  
    t0 = time.time()  
    for step in pipeline.stream(s):  
        node = list(step.keys())[0]  
        elapsed = time.time() - t0  
        print(f"[{elapsed:.0f}s] node={node}", flush=True)  
print("starting stream...", flush=True)  
asyncio.run(run())  
print("all done", flush=True) 
