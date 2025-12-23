import sys
import os
import asyncio

# --- 1. Setup Environment to find your app code ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.database.connection import SessionLocal, engine
from src.database.models import Exercise, Base
from sqlalchemy import text

# Try to import OpenAI for embeddings
try:
    from openai import OpenAI
    # EXPECTS API KEY IN ENVIRONMENT VARIABLE: export OPENAI_API_KEY="sk-..."
    client = OpenAI() 
    HAS_OPENAI = True
    print("✅ OpenAI Library found. Will attempt to generate real embeddings.")
except ImportError:
    HAS_OPENAI = False
    print("⚠️ OpenAI Library not found. Using dummy vectors.")
except Exception as e:
    HAS_OPENAI = False
    print(f"⚠️ OpenAI Warning: {e}. Using dummy vectors.")

# --- 2. The Exercise Data (The "Golden Standard") ---
exercises_data = [
    # --- UPPER BODY PUSH ---
    {
        "name": "Barbell Bench Press",
        "target_zone": "Upper",
        "force_type": "Push",
        "muscle_group": "Chest",
        "secondary_muscles": ["Triceps", "Front Delts"],
        "mechanics": "Compound",
        "equipment": ["Barbell", "Bench"],
        "difficulty": "Intermediate",
        "category": "Strength",
        "instructions": "Lie on back, lower bar to mid-chest, press up explosively.",
        "contraindications": ["shoulder_impingement"]
    },
    {
        "name": "Overhead Press",
        "target_zone": "Upper",
        "force_type": "Push",
        "muscle_group": "Shoulders",
        "secondary_muscles": ["Triceps", "Core"],
        "mechanics": "Compound",
        "equipment": ["Barbell"],
        "difficulty": "Intermediate",
        "category": "Strength",
        "instructions": "Press bar from collarbone to overhead lockout. Keep core tight.",
        "contraindications": ["lower_back_pain"]
    },
    
    # --- UPPER BODY PULL ---
    {
        "name": "Pull Up",
        "target_zone": "Upper",
        "force_type": "Pull",
        "muscle_group": "Lats",
        "secondary_muscles": ["Biceps", "Rear Delts"],
        "mechanics": "Compound",
        "equipment": ["Pull-up Bar"],
        "difficulty": "Advanced",
        "category": "Strength",
        "instructions": "Hang from bar, pull chest to bar, lower slowly.",
        "contraindications": ["shoulder_instability"]
    },
    {
        "name": "Dumbbell Row",
        "target_zone": "Upper",
        "force_type": "Pull",
        "muscle_group": "Back",
        "secondary_muscles": ["Biceps"],
        "mechanics": "Isolation", # Often debated, but safe to classify as isolation/accessory
        "equipment": ["Dumbbell", "Bench"],
        "difficulty": "Beginner",
        "category": "Hypertrophy",
        "instructions": "Support on bench, row dumbbell to hip pocket.",
        "contraindications": []
    },

    # --- LOWER BODY SQUAT (Knee Dominant) ---
    {
        "name": "Barbell Back Squat",
        "target_zone": "Lower",
        "force_type": "Squat",
        "muscle_group": "Quadriceps",
        "secondary_muscles": ["Glutes", "Lower Back"],
        "mechanics": "Compound",
        "equipment": ["Barbell", "Rack"],
        "difficulty": "Advanced",
        "category": "Strength",
        "instructions": "Bar on upper back, squat deep, drive up through mid-foot.",
        "contraindications": ["knee_pain", "herniated_disc"]
    },
    
    # --- LOWER BODY HINGE (Hip Dominant) ---
    {
        "name": "Romanian Deadlift",
        "target_zone": "Lower",
        "force_type": "Hinge",
        "muscle_group": "Hamstrings",
        "secondary_muscles": ["Glutes", "Lower Back"],
        "mechanics": "Compound",
        "equipment": ["Barbell"],
        "difficulty": "Intermediate",
        "category": "Strength",
        "instructions": "Hinge at hips, keep legs slightly bent, lower bar to mid-shin.",
        "contraindications": ["sciatica", "lower_back_pain"]
    },

    # --- LOWER BODY LUNGE (Unilateral) ---
    {
        "name": "Bulgarian Split Squat",
        "target_zone": "Lower",
        "force_type": "Lunge",
        "muscle_group": "Quadriceps",
        "secondary_muscles": ["Glutes", "Stabilizers"],
        "mechanics": "Compound",
        "equipment": ["Dumbbell", "Bench"],
        "difficulty": "Advanced",
        "category": "Hypertrophy",
        "instructions": "Rear foot on bench, lower knee to floor, drive up.",
        "contraindications": ["balance_issues"]
    },

    # --- CORE ---
    {
        "name": "Plank",
        "target_zone": "Core",
        "force_type": "Static",
        "muscle_group": "Abs",
        "secondary_muscles": ["Shoulders"],
        "mechanics": "Isolation",
        "equipment": ["Bodyweight"],
        "difficulty": "Beginner",
        "category": "Stability",
        "instructions": "Hold push-up position on elbows. Keep body straight.",
        "contraindications": []
    }
]

# --- 3. Helper Functions ---

def get_embedding(text_input):
    """Generates vector from OpenAI, or returns zeros if fails"""
    if HAS_OPENAI and os.environ.get("OPENAI_API_KEY"):
        try:
            # Using the new small model (efficient & cheap)
            response = client.embeddings.create(
                input=text_input,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Error generating embedding for {text_input[:10]}...: {e}")
            return [0.0] * 1536
    else:
        # Return a Dummy Vector (1536 zeros)
        return [0.0] * 1536

def seed_db():
    print("🌱 Starting Database Seeding...")
    db = SessionLocal()
    
    try:
        # Optional: Clear existing data to avoid duplicates
        # db.query(Exercise).delete()
        # db.commit()
        
        for data in exercises_data:
            # Check if exists
            exists = db.query(Exercise).filter_by(name=data["name"]).first()
            if exists:
                print(f"🔹 {data['name']} already exists. Skipping.")
                continue

            # Create 'rich' description for the AI to read later
            # "Barbell Bench Press is a Upper Body Push exercise for Chest..."
            semantic_text = f"{data['name']} is a {data['target_zone']} {data['force_type']} exercise targeting {data['muscle_group']}."
            
            # Generate Vector
            vector = get_embedding(semantic_text)
            
            # Create Object
            new_exercise = Exercise(
                name=data["name"],
                target_zone=data["target_zone"],
                force_type=data["force_type"],
                muscle_group=data["muscle_group"],
                secondary_muscles=data.get("secondary_muscles", []),
                mechanics=data["mechanics"],
                equipment=data["equipment"],
                difficulty=data["difficulty"],
                category=data["category"],
                instructions=data["instructions"],
                contraindications=data.get("contraindications", []),
                embedding=vector
            )
            
            db.add(new_exercise)
            print(f"✅ Added: {data['name']} ({data['force_type']})")

        db.commit()
        print("🎉 Database seeded successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()