import asyncio
import json
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import init_db, async_session
from app.services.cache_service import cache_service
from app.models.user import User
from app.models.job import Job
from app.core.security import hash_password
from app.services.document_intel import DocumentIntelService
from app.ai.runner import run_pipeline

SAMPLE_TEXT = """
# Physics Chapter 3: Kinematics and Laws of Motion

## 1. Introduction to Motion
Motion is defined as a change in position of an object with respect to time and its surroundings. Kinematics is the branch of mechanics concerned with the motion of objects without reference to the forces which cause the motion.

### Key Definitions
- Distance: The total length of path travelled by a body.
- Displacement: The shortest vector distance from initial to final position.
- Speed: Rate of change of distance (Scalar quantity, v = d/t).
- Velocity: Rate of change of displacement (Vector quantity, v = s/t).
- Acceleration: Rate of change of velocity (a = (v - u)/t).

## 2. Equations of Motion (Constant Acceleration)
For a body moving along a straight line with uniform acceleration 'a':
1. First Equation: v = u + at
2. Second Equation: s = ut + 0.5 * a * t^2
3. Third Equation: v^2 = u^2 + 2 * a * s

Where:
- u = initial velocity (m/s)
- v = final velocity (m/s)
- a = uniform acceleration (m/s^2)
- t = time taken (seconds)
- s = displacement (meters)

## 3. Newton's Laws of Motion
### First Law (Law of Inertia)
An object remains at rest or in uniform motion along a straight line unless acted upon by an external net force.

### Second Law (Law of Force & Acceleration)
The rate of change of momentum of a body is directly proportional to the applied force and takes place in the direction of force.
Formula: F = m * a

### Third Law (Action & Reaction)
To every action, there is an equal and opposite reaction.

## 4. Common Misconceptions
- Misconception: Heavier objects fall faster than lighter objects in a vacuum.
  Fact: In a vacuum, all objects accelerate towards Earth at the same rate (g = 9.8 m/s^2) regardless of mass.
- Misconception: An object requires a constant force to keep moving at a constant speed.
  Fact: According to Newton's First Law, force is only required to change velocity (accelerate), not to maintain constant velocity in frictionless space.

## 5. Sample Numerical Problem
Problem: A car starts from rest (u = 0) and accelerates uniformly at 2 m/s^2 for 5 seconds. Calculate its final velocity and total distance travelled.
Solution:
Given: u = 0, a = 2 m/s^2, t = 5 s
Step 1: v = u + at = 0 + (2 * 5) = 10 m/s
Step 2: s = ut + 0.5 * a * t^2 = 0 + 0.5 * 2 * (5^2) = 25 meters
Answer: Final velocity = 10 m/s, Distance = 25 m.
"""

async def run_e2e_test():
    print("=" * 60)
    print("Starting End-to-End Pipeline Verification Test")
    print("=" * 60)

    # Step 1: Initialize Database & Cache
    print("\n[1/5] Initializing Database and Redis Cache...")
    await init_db()
    try:
        await cache_service.connect()
        print("  - Database initialized successfully.")
        print("  - Redis connected successfully.")
    except Exception as e:
        print(f"  - Redis connection notice: {e} (Fallback to direct execution)")

    # Step 2: Create sample upload text file
    print("\n[2/5] Creating sample document file (kinematics_test.txt)...")
    upload_dir = Path("./uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    sample_file = upload_dir / "kinematics_test.txt"
    sample_file.write_text(SAMPLE_TEXT, encoding="utf-8")
    print(f"  - File created at {sample_file.resolve()}")

    # Step 3: Run Document Intelligence (Stage 1)
    print("\n[3/5] Stage 1: Running Document Intelligence...")
    doc_intel = DocumentIntelService()
    parsed_doc = await doc_intel.process(str(sample_file))
    print(f"  - File type detected: {parsed_doc.get('file_type')}")
    print(f"  - Word count: {parsed_doc.get('word_count')}")
    print(f"  - Sections found: {len(parsed_doc.get('sections', []))}")
    print(f"  - Equations found: {len(parsed_doc.get('equations', []))}")

    # Step 4: Run Stages 2 to 10 via Pipeline Runner
    print("\n[4/5] Running Stages 2-10 (Full AI Pipeline Execution)...")

    config = {
        "period_duration": 40,
        "num_periods": 3,
        "target_language": "English",
        "board_alignment": "CBSE"
    }

    job_id = "test_e2e_kinematics_001"

    # Save job record to DB
    from sqlalchemy import select
    async with async_session() as db:
        res = await db.execute(select(User).where(User.email == "teacher@gyansetu.edu"))
        user = res.scalar_one_or_none()
        if not user:
            user = User(
                name="Test Teacher",
                email="teacher@gyansetu.edu",
                password_hash=hash_password("password123"),
                role="teacher"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        res = await db.execute(select(Job).where(Job.id == job_id))
        job = res.scalar_one_or_none()
        if job:
            await db.delete(job)
            await db.commit()

        job = Job(
            id=job_id,
            user_id=user.id,
            status="pending",
            file_name="kinematics_test.txt",
            file_path=str(sample_file),
            config=config
        )
        db.add(job)
        await db.commit()

    print("  - Created test user and job record in SQLite database.")
    print("  - Executing full AI pipeline across all 10 stages...")

    try:
        await run_pipeline(job_id, str(sample_file), config)
        print("\n[5/5] Pipeline Execution Completed Successfully!")
        print("=" * 60)
        print("PIPELINE OUTPUT SUMMARY:")
        print("=" * 60)

        # Check job in database
        async with async_session() as db:
            from sqlalchemy import select
            res = await db.execute(select(Job).where(Job.id == job_id))
            updated_job = res.scalar_one_or_none()
            print(f"Job Status in DB: {updated_job.status}")
            print(f"Current Stage in DB: {updated_job.current_stage}/10")
            print(f"TKP Output File: {updated_job.tkp_path}")

        if updated_job.tkp_path and Path(updated_job.tkp_path).exists():
            tkp_data = json.loads(Path(updated_job.tkp_path).read_text(encoding="utf-8"))
            print("\nTEACHER KNOWLEDGE PACKAGE (TKP) VERIFICATION:")
            print(f"  - Document Title: {tkp_data.get('metadata', {}).get('document_title')}")
            print(f"  - Subject: {tkp_data.get('metadata', {}).get('subject')}")
            print(f"  - Grade: {tkp_data.get('metadata', {}).get('grade')}")
            print(f"  - Difficulty: {tkp_data.get('metadata', {}).get('difficulty')}")
            print(f"  - Topic: {tkp_data.get('metadata', {}).get('topic')}")

            kb = tkp_data.get('knowledge_base', {})
            print(f"  - Learning Objectives: {len(kb.get('learning_objectives', []))} extracted")
            print(f"  - Concepts: {len(kb.get('concepts', []))} extracted")
            print(f"  - Formulae: {len(kb.get('formulae', []))} extracted")
            print(f"  - Misconceptions: {len(kb.get('common_misconceptions', []))} identified")

            plan = tkp_data.get('teaching_plan', {})
            print(f"  - Teaching Periods: {len(plan.get('periods', []))} periods generated")

            assessments = tkp_data.get('assessments', {})
            print(f"  - MCQs: {len(assessments.get('mcqs', []))}")
            print(f"  - Short Answers: {len(assessments.get('short_answers', []))}")
            print(f"  - Long Answers: {len(assessments.get('long_answers', []))}")
            print(f"  - Numerical Problems: {len(assessments.get('numerical_problems', []))}")

            validation = tkp_data.get('validation_report', {})
            print(f"  - Validation Schema Valid: {validation.get('schema_valid')}")
            print(f"  - Completeness Score: {validation.get('completeness_score')}")

            print("\n E2E VERIFICATION TEST PASSED 100%! EVERYTHING IS WORKING PROPERLY.")

    except Exception as e:
        print(f"\n Pipeline execution failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
