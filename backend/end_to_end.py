"""End-to-end pipeline test: start server, upload file, verify stages."""
import multiprocessing
import os
import signal
import subprocess
import sys
import time
import httpx
import dotenv

dotenv.load_dotenv()

BASE = "http://127.0.0.1:8000"

def start_server():
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc

def wait_for_server(timeout=30):
    for _ in range(timeout * 2):
        try:
            r = httpx.get(f"{BASE}/api/jobs/health", timeout=5)
            return True
        except Exception:
            time.sleep(0.5)
    return False

def main():
    # 1. Start server
    print("Starting server...", flush=True)
    proc = start_server()
    if not wait_for_server():
        print("FAIL: Server did not start", flush=True)
        proc.kill()
        sys.exit(1)
    print("Server is up.", flush=True)

    try:
        # 2. Register + login
        email = f"e2e_{int(time.time())}@test.ai"
        password = "TestPass123!"
        print(f"Registering {email}...", flush=True)
        r = httpx.post(f"{BASE}/api/auth/register", json={
            "email": email, "password": password, "name": "E2E Test"
        })
        assert r.status_code == 200, f"Register failed: {r.status_code} {r.text}"
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Registered + logged in.", flush=True)

        # 3. Upload a .txt file
        test_file = os.path.join(os.path.dirname(__file__), "test_upload.txt")
        with open(test_file, "w") as f:
            f.write("""Machine Learning Fundamentals

Supervised learning is a type of machine learning where the model is trained on labeled data.
Common algorithms include linear regression, decision trees, and neural networks.

Deep Learning
Neural networks with many layers form the basis of deep learning.
These models excel at image recognition, natural language processing, and other complex tasks.

Key Concepts
- Training: the process of teaching a model using data
- Inference: using a trained model to make predictions
- Overfitting: when a model memorizes training data but fails on new data
""")

        print("Uploading file...", flush=True)
        with open(test_file, "rb") as f:
            r = httpx.post(
                f"{BASE}/api/upload",
                headers=headers,
                files={"file": ("test_upload.txt", f, "text/plain")},
                data={"period_duration": 40, "subject": "machine learning", "topic": "supervised learning"},
            )
        print(f"Upload response: {r.status_code}", flush=True)

        if r.status_code == 200:
            job_id = r.json().get("job_id")
            print(f"Job created: {job_id}", flush=True)

            # 4. Poll job status
            stages_found = set()
            for _ in range(60):
                r = httpx.get(f"{BASE}/api/jobs/{job_id}", headers=headers, timeout=30)
                if r.status_code != 200:
                    time.sleep(2)
                    continue
                data = r.json()
                stage = data.get("current_stage", 0)
                stages_found.add(stage)
                status = data.get("status")
                print(f"  stage={stage} status={status}", flush=True)
                if status == "completed":
                    print(f"ALL STAGES SEEN: {sorted(stages_found)}", flush=True)
                    print(f"RESULT: {data.get('result', {})}", flush=True)
                    break
                if status in ("failed", "error"):
                    print(f"FAILED: {data}", flush=True)
                    break
                time.sleep(2)
            else:
                print("Timed out waiting for completion", flush=True)
        else:
            print(f"Upload failed: {r.text}", flush=True)

    finally:
        proc.kill()
        proc.wait()
        print("Server stopped.", flush=True)

if __name__ == "__main__":
    main()
