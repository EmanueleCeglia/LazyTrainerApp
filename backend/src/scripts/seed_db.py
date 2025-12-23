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
    # =========================================================================
    # UPPER BODY PUSH (Force: Push)
    # Muscles: Chest, Shoulders, Triceps
    # =========================================================================
    {
        "name": "Push-Up (Standard)",
        "target_zone": "Upper",
        "force_type": "Push",
        "muscle_group": "Chest",
        "secondary_muscles": ["Triceps", "Front Delts", "Core"],
        "mechanics": "Compound",
        "equipment": ["Bodyweight"],
        "difficulty": "Beginner",
        "category": "Strength",
        "instructions": "Place hands shoulder-width, lower chest to floor, push back up keeping body rigid.",
        "contraindications": ["wrist_pain", "shoulder_injury"]
    },
    {
        "name": "Diamond Push-Up",
        "target_zone": "Upper",
        "force_type": "Push",
        "muscle_group": "Triceps",
        "secondary_muscles": ["Chest", "Front Delts"],
        "mechanics": "Compound",
        "equipment": ["Bodyweight"],
        "difficulty": "Intermediate",
        "category": "Strength",
        "instructions": "Hands close forming a diamond, lower chest to hands, push up focusing on triceps.",
        "contraindications": ["wrist_pain", "elbow_tendonitis"]
    },
    {
        "name": "Pike Push-Up",
        "target_zone": "Upper",
        "force_type": "Push",
        "muscle_group": "Shoulders",
        "secondary_muscles": ["Triceps", "Upper Chest"],
        "mechanics": "Compound",
        "equipment": ["Bodyweight"],
        "difficulty": "Intermediate",
        "category": "Strength",
        "instructions": "Downward dog position, lower head to floor, press back up vertically.",
        "contraindications": ["high_blood_pressure", "shoulder_impingement"]
    },
    {
        "name": "Dips",
        "target_zone": "Upper",
        "force_type": "Push",
        "muscle_group": "Triceps",
        "secondary_muscles": ["Lower Chest", "Front Delts"],
        "mechanics": "Compound",
        "equipment": ["Parallel Bars", "Dip Station"],
        "difficulty": "Intermediate",
        "category": "Strength",
        "instructions": "Lower body until shoulders are below elbows, push back up to lockout.",
        "contraindications": ["shoulder_instability", "rotator_cuff_injury"]
    },
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
        "instructions": "Lie on bench, lower bar to mid-chest, press explosively upward.",
        "contraindications": ["shoulder_impingement", "pec_tear_recovery"]
    },
    {
        "name": "Incline Dumbbell Press",
        "target_zone": "Upper",
        "force_type": "Push",
        "muscle_group": "Chest",
        "secondary_muscles": ["Triceps", "Front Delts"],
        "mechanics": "Compound",
        "equipment": ["Dumbbells", "Incline Bench"],
        "difficulty": "Intermediate",
        "category": "Strength",
        "instructions": "Bench set to 30-45 degrees, press weights straight up from shoulders.",
        "contraindications": ["shoulder_instability"]
    },
    {
        "name": "Overhead Press (Military Press)",
        "target_zone": "Upper",
        "force_type": "Push",
        "muscle_group": "Shoulders",
        "secondary_muscles": ["Triceps", "Upper Chest", "Core"],
        "mechanics": "Compound",
        "equipment": ["Barbell"],
        "difficulty": "Intermediate",
        "category": "Strength",
        "instructions": "Press bar from collarbone to overhead lockout, keeping core tight.",
        "contraindications": ["lower_back_pain", "shoulder_impingement"]
    },
    {
        "name": "Lateral Raises",
        "target_zone": "Upper",
        "force_type": "Push",
        "muscle_group": "Shoulders",
        "secondary_muscles": ["Traps"],
        "mechanics": "Isolation",
        "equipment": ["Dumbbells"],
        "difficulty": "Beginner",
        "category": "Hypertrophy",
        "instructions": "Raise weights to sides until shoulder height, control the descent.",
        "contraindications": ["shoulder_impingement"]
    },
    {
        "name": "Tricep Pushdown",
        "target_zone": "Upper",
        "force_type": "Push",
        "muscle_group": "Triceps",
        "secondary_muscles": [],
        "mechanics": "Isolation",
        "equipment": ["Cable Machine", "Rope"],
        "difficulty": "Beginner",
        "category": "Hypertrophy",
        "instructions": "Keep elbows fixed at sides, extend arms downward fully.",
        "contraindications": ["elbow_tendonitis"]
    },
    {
        "name": "Cable Crossover",
        "target_zone": "Upper",
        "force_type": "Push",
        "muscle_group": "Chest",
        "secondary_muscles": ["Front Delts"],
        "mechanics": "Isolation",
        "equipment": ["Cable Machine"],
        "difficulty": "Intermediate",
        "category": "Hypertrophy",
        "instructions": "Pull handles together in bear-hug motion, squeeze pecs at center.",
        "contraindications": ["shoulder_instability"]
    },

    # =========================================================================
    # UPPER BODY PULL (Force: Pull)
    # Muscles: Back, Biceps, Rear Delts
    # =========================================================================
    {
        "name": "Pull-Up",
        "target_zone": "Upper",
        "force_type": "Pull",
        "muscle_group": "Back",
        "secondary_muscles": ["Biceps", "Forearms"],
        "mechanics": "Compound",
        "equipment": ["Pull-up Bar"],
        "difficulty": "Advanced",
        "category": "Strength",
        "instructions": "Overhand grip, pull chin over bar, lower all the way down.",
        "contraindications": ["shoulder_injury", "elbow_tendonitis"]
    },
    {
        "name": "Chin-Up",
        "target_zone": "Upper",
        "force_type": "Pull",
        "muscle_group": "Back",
        "secondary_muscles": ["Biceps", "Forearms"],
        "mechanics": "Compound",
        "equipment": ["Pull-up Bar"],
        "difficulty": "Intermediate",
        "category": "Strength",
        "instructions": "Underhand grip, pull chin over bar, lower fully.",
        "contraindications": ["wrist_pain", "elbow_tendonitis"]
    },
    {
        "name": "Inverted Row",
        "target_zone": "Upper",
        "force_type": "Pull",
        "muscle_group": "Back",
        "secondary_muscles": ["Biceps", "Rear Delts"],
        "mechanics": "Compound",
        "equipment": ["Bar", "TRX"],
        "difficulty": "Beginner",
        "category": "Strength",
        "instructions": "Hang under bar, keep body straight, pull chest to bar.",
        "contraindications": ["lower_back_pain"]
    },
    {
        "name": "Lat Pulldown",
        "target_zone": "Upper",
        "force_type": "Pull",
        "muscle_group": "Back",
        "secondary_muscles": ["Biceps", "Rear Delts"],
        "mechanics": "Compound",
        "equipment": ["Cable Machine"],
        "difficulty": "Beginner",
        "category": "Hypertrophy",
        "instructions": "Pull bar down to upper chest, squeeze lats, return slowly.",
        "contraindications": ["shoulder_impingement"]
    },
    {
        "name": "Barbell Bent-Over Row",
        "target_zone": "Upper",
        "force_type": "Pull",
        "muscle_group": "Back",
        "secondary_muscles": ["Biceps", "Lower Back"],
        "mechanics": "Compound",
        "equipment": ["Barbell"],
        "difficulty": "Intermediate",
        "category": "Strength",
        "instructions": "Hinge at hips, flat back, pull bar to stomach.",
        "contraindications": ["lower_back_herniation", "sciatica"]
    },
    {
        "name": "Seated Cable Row",
        "target_zone": "Upper",
        "force_type": "Pull",
        "muscle_group": "Back",
        "secondary_muscles": ["Biceps", "Rhomboids"],
        "mechanics": "Compound",
        "equipment": ["Cable Machine"],
        "difficulty": "Beginner",
        "category": "Hypertrophy",
        "instructions": "Sit tall, pull handle to abdomen, squeeze shoulder blades back.",
        "contraindications": ["lower_back_pain"]
    },
    {
        "name": "Face Pull",
        "target_zone": "Upper",
        "force_type": "Pull",
        "muscle_group": "Shoulders",
        "secondary_muscles": ["Rear Delts", "Rotator Cuff"],
        "mechanics": "Isolation",
        "equipment": ["Cable Machine", "Rope"],
        "difficulty": "Intermediate",
        "category": "Corrective",
        "instructions": "Pull rope to face, separating hands and rotating forearms up.",
        "contraindications": ["shoulder_impingement"]
    },
    {
        "name": "Dumbbell Bicep Curl",
        "target_zone": "Upper",
        "force_type": "Pull",
        "muscle_group": "Biceps",
        "secondary_muscles": ["Forearms"],
        "mechanics": "Isolation",
        "equipment": ["Dumbbells"],
        "difficulty": "Beginner",
        "category": "Hypertrophy",
        "instructions": "Curl weights to shoulders, keeping elbows at sides.",
        "contraindications": ["elbow_tendonitis"]
    },

    # =========================================================================
    # LOWER BODY: SQUAT PATTERN (Knee Dominant)
    # Muscles: Quads, Glutes
    # =========================================================================
    {
        "name": "Air Squat",
        "target_zone": "Lower",
        "force_type": "Squat",
        "muscle_group": "Quadriceps",
        "secondary_muscles": ["Glutes", "Hamstrings"],
        "mechanics": "Compound",
        "equipment": ["Bodyweight"],
        "difficulty": "Beginner",
        "category": "Endurance",
        "instructions": "Feet shoulder-width, sit hips back and down, stand back up.",
        "contraindications": ["knee_pain", "hip_impingement"]
    },
    {
        "name": "Barbell Back Squat",
        "target_zone": "Lower",
        "force_type": "Squat",
        "muscle_group": "Quadriceps",
        "secondary_muscles": ["Glutes", "Hamstrings", "Core"],
        "mechanics": "Compound",
        "equipment": ["Barbell", "Rack"],
        "difficulty": "Intermediate",
        "category": "Strength",
        "instructions": "Bar on upper back, deep squat maintaining spine neutrality, drive up.",
        "contraindications": ["spinal_injury", "knee_injury"]
    },
    {
        "name": "Leg Press",
        "target_zone": "Lower",
        "force_type": "Squat",
        "muscle_group": "Quadriceps",
        "secondary_muscles": ["Glutes"],
        "mechanics": "Compound",
        "equipment": ["Leg Press Machine"],
        "difficulty": "Beginner",
        "category": "Strength",
        "instructions": "Push platform away with feet, avoid locking knees at top.",
        "contraindications": ["lower_back_pain"]
    },
    {
        "name": "Leg Extension",
        "target_zone": "Lower",
        "force_type": "Squat",
        "muscle_group": "Quadriceps",
        "secondary_muscles": [],
        "mechanics": "Isolation",
        "equipment": ["Leg Extension Machine"],
        "difficulty": "Beginner",
        "category": "Hypertrophy",
        "instructions": "Extend legs until straight, focusing solely on quads.",
        "contraindications": ["knee_ligament_injury"]
    },

    # =========================================================================
    # LOWER BODY: HINGE PATTERN (Hip Dominant)
    # Muscles: Hamstrings, Glutes, Lower Back
    # =========================================================================
    {
        "name": "Romanian Deadlift (RDL)",
        "target_zone": "Lower",
        "force_type": "Hinge",
        "muscle_group": "Hamstrings",
        "secondary_muscles": ["Glutes", "Lower Back"],
        "mechanics": "Compound",
        "equipment": ["Barbell", "Dumbbells"],
        "difficulty": "Intermediate",
        "category": "Strength",
        "instructions": "Slight knee bend, hinge at hips sending butt back, feel hamstring stretch, return.",
        "contraindications": ["lower_back_pain", "sciatica"]
    },
    {
        "name": "Glute Bridge",
        "target_zone": "Lower",
        "force_type": "Hinge",
        "muscle_group": "Glutes",
        "secondary_muscles": ["Hamstrings", "Core"],
        "mechanics": "Isolation",
        "equipment": ["Bodyweight"],
        "difficulty": "Beginner",
        "category": "Activation",
        "instructions": "Lie on back, lift hips to ceiling, squeeze glutes at top.",
        "contraindications": ["acute_lower_back_pain"]
    },
    {
        "name": "Hip Thrust",
        "target_zone": "Lower",
        "force_type": "Hinge",
        "muscle_group": "Glutes",
        "secondary_muscles": ["Hamstrings"],
        "mechanics": "Compound",
        "equipment": ["Bench", "Barbell"],
        "difficulty": "Intermediate",
        "category": "Strength",
        "instructions": "Upper back on bench, weight on hips, drive hips upward to extension.",
        "contraindications": ["lower_back_pain"]
    },
    {
        "name": "Superman",
        "target_zone": "Lower", # Often grouped with Back, but technically a Posterior Chain Hinge
        "force_type": "Hinge",
        "muscle_group": "Lower Back",
        "secondary_muscles": ["Glutes", "Hamstrings"],
        "mechanics": "Isolation",
        "equipment": ["Bodyweight"],
        "difficulty": "Beginner",
        "category": "Stability",
        "instructions": "Lie prone, lift arms and legs, holding the arch.",
        "contraindications": ["acute_lower_back_pain"]
    },
    # Note: Leg Curl is technically Knee Flexion, but for programming purposes,
    # it is often grouped with Hinge days to balance Quads (Squat).
    {
        "name": "Leg Curl", 
        "target_zone": "Lower",
        "force_type": "Hinge", # Categorized here to ensure Hamstring selection
        "muscle_group": "Hamstrings",
        "secondary_muscles": [],
        "mechanics": "Isolation",
        "equipment": ["Leg Curl Machine"],
        "difficulty": "Beginner",
        "category": "Hypertrophy",
        "instructions": "Curl legs against resistance towards glutes.",
        "contraindications": ["knee_injury"]
    },

    # =========================================================================
    # LOWER BODY: LUNGE PATTERN (Unilateral)
    # Muscles: Quads, Glutes, Stabilizers
    # =========================================================================
    {
        "name": "Walking Lunge",
        "target_zone": "Lower",
        "force_type": "Lunge",
        "muscle_group": "Quadriceps",
        "secondary_muscles": ["Glutes", "Calves"],
        "mechanics": "Compound",
        "equipment": ["Bodyweight", "Dumbbells"],
        "difficulty": "Intermediate",
        "category": "Hypertrophy",
        "instructions": "Step forward, drop back knee, drive up into next step.",
        "contraindications": ["knee_pain", "balance_issues"]
    },
    {
        "name": "Bulgarian Split Squat",
        "target_zone": "Lower",
        "force_type": "Lunge",
        "muscle_group": "Quadriceps",
        "secondary_muscles": ["Glutes", "Balance"],
        "mechanics": "Compound",
        "equipment": ["Bench", "Dumbbells"],
        "difficulty": "Advanced",
        "category": "Hypertrophy",
        "instructions": "Rear foot on bench, squat down with front leg, push back up.",
        "contraindications": ["knee_pain", "poor_balance"]
    },

    # =========================================================================
    # CORE: STATIC (Anti-Movement/Stability)
    # =========================================================================
    {
        "name": "Plank",
        "target_zone": "Core",
        "force_type": "Static",
        "muscle_group": "Rectus Abdominis",
        "secondary_muscles": ["Transverse Abdominis", "Shoulders"],
        "mechanics": "Isolation",
        "equipment": ["Bodyweight"],
        "difficulty": "Beginner",
        "category": "Stability",
        "instructions": "Hold top of pushup position (or elbows), resist gravity, no sagging.",
        "contraindications": ["lower_back_pain", "shoulder_pain"]
    },
    {
        "name": "Side Plank",
        "target_zone": "Core",
        "force_type": "Static",
        "muscle_group": "Obliques",
        "secondary_muscles": ["Shoulders"],
        "mechanics": "Isolation",
        "equipment": ["Bodyweight"],
        "difficulty": "Beginner",
        "category": "Stability",
        "instructions": "Balance on one forearm and side of foot, hold hips high.",
        "contraindications": ["shoulder_pain"]
    },

    # =========================================================================
    # CORE: DYNAMIC (Flexion/Rotation)
    # =========================================================================
    {
        "name": "Hanging Leg Raise",
        "target_zone": "Core",
        "force_type": "Dynamic",
        "muscle_group": "Rectus Abdominis",
        "secondary_muscles": ["Hip Flexors"],
        "mechanics": "Compound",
        "equipment": ["Pull-up Bar"],
        "difficulty": "Advanced",
        "category": "Strength",
        "instructions": "Hang from bar, lift legs to 90 degrees or higher, control the drop.",
        "contraindications": ["lower_back_pain", "shoulder_injury"]
    },
    {
        "name": "Russian Twist",
        "target_zone": "Core",
        "force_type": "Dynamic",
        "muscle_group": "Obliques",
        "secondary_muscles": ["Rectus Abdominis"],
        "mechanics": "Compound",
        "equipment": ["Medicine Ball", "Bodyweight"],
        "difficulty": "Intermediate",
        "category": "Rotational",
        "instructions": "Sit in V-shape, rotate torso side to side tapping the floor.",
        "contraindications": ["lower_back_pain", "herniated_disc"]
    },
    {
        "name": "Bicycle Crunch",
        "target_zone": "Core",
        "force_type": "Dynamic",
        "muscle_group": "Obliques",
        "secondary_muscles": ["Rectus Abdominis"],
        "mechanics": "Isolation",
        "equipment": ["Bodyweight"],
        "difficulty": "Beginner",
        "category": "Endurance",
        "instructions": "Lie on back, alternate elbow to opposite knee in pedaling motion.",
        "contraindications": ["neck_pain"]
    },
    {
        "name": "Ab Wheel Rollout",
        "target_zone": "Core",
        "force_type": "Dynamic",
        "muscle_group": "Rectus Abdominis",
        "secondary_muscles": ["Lats"],
        "mechanics": "Compound",
        "equipment": ["Ab Wheel"],
        "difficulty": "Advanced",
        "category": "Strength",
        "instructions": "Roll wheel forward extending body, pull back using abs.",
        "contraindications": ["lower_back_pain"]
    },
    {
        "name": "Cable Woodchopper",
        "target_zone": "Core",
        "force_type": "Dynamic",
        "muscle_group": "Obliques",
        "secondary_muscles": ["Shoulders"],
        "mechanics": "Compound",
        "equipment": ["Cable Machine"],
        "difficulty": "Intermediate",
        "category": "Rotational",
        "instructions": "Pull cable diagonally across body, pivoting back foot.",
        "contraindications": ["lower_back_pain"]
    },
    
    # =========================================================================
    # SPECIAL CASE: CALVES
    # =========================================================================
    {
        "name": "Standing Calf Raise",
        "target_zone": "Lower",
        # Calves don't fit Squat/Hinge/Lunge. We use 'Push' as it is Ankle Extension (pushing ground).
        "force_type": "Push", 
        "muscle_group": "Calves",
        "secondary_muscles": [],
        "mechanics": "Isolation",
        "equipment": ["Machine", "Step"],
        "difficulty": "Beginner",
        "category": "Hypertrophy",
        "instructions": "Elevate heels, lower down for stretch, drive up onto toes.",
        "contraindications": ["plantar_fasciitis", "ankle_instability"]
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