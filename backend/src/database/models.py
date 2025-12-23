from sqlalchemy import Column, Integer, String, Text, ARRAY, Float, Boolean
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    
    # --- Identification ---
    name = Column(String, unique=True, nullable=False)
    
    # --- Biomechanics (The "Brain" of the schema) ---
    # 1. Broad Category (Upper, Lower, Core, Full Body) -> New!
    target_zone = Column(String, nullable=False)
    
    # 2. Functional Pattern (Push, Pull, Static, Hinge, Squat, Lunge)
    force_type = Column(String, nullable=True)
    
    # 3. Specific Anatomy (Chest, Quads, Hamstrings, Lats, etc.)
    muscle_group = Column(String, nullable=False)
    secondary_muscles = Column(ARRAY(String))
    
    # 4. Complexity (Compound vs Isolation)
    mechanics = Column(String, nullable=True)
    
    category = Column(String, nullable=False) # Strength, Cardio, Plyo
    
    # --- Logistics ---
    equipment = Column(ARRAY(String), nullable=False)
    difficulty = Column(String, nullable=False)
    
    # --- Content ---
    instructions = Column(Text, nullable=False)
    video_url = Column(String, nullable=True)
    
    # --- Safety ---
    contraindications = Column(ARRAY(String))           
    
    # --- RAG ---
    embedding = Column(Vector(1536)) 

class UserProfile(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    age = Column(Integer)
    gender = Column(String)
    weight = Column(Float)
    height = Column(Float)
    experience_level = Column(String)
    injuries = Column(ARRAY(String))
    equipment_available = Column(ARRAY(String))
    goals = Column(ARRAY(String))






# Comments about force_type
# If we restrict `force_type` to only `Push`, `Pull`, and `Static`, the AI will struggle to build balanced leg workouts.

# For example, a **Squat** and a **Deadlift** are technically both "Legs," but they train completely different movement patterns (Knee vs. Hip). If the AI just sees "Push" or "Pull," it might mistakenly prescribe 3 Squat variations and 0 Hamstring exercises in a single session.

# I strongly recommend using a **Hybrid Approach** for your `force_type` column. This aligns with modern Strength & Conditioning standards.

# ### The Recommended Taxonomy

# We should allow `force_type` to contain the following values. This gives the AI the specific vocabulary it needs to "think" like a coach.

# #### 1. Upper Body: Keep "Push / Pull"

# For the upper body, the distinction is simple and effective.

# * **`Push`**: Moving weight away from the body.
# * *Muscles:* Chest, Shoulders, Triceps.
# * *Examples:* Bench Press, Overhead Press, Push-ups.


# * **`Pull`**: Bringing weight toward the body.
# * *Muscles:* Back, Biceps, Rear Delts.
# * *Examples:* Pull-ups, Rows, Face Pulls.



# #### 2. Lower Body: Use "Patterns" (Squat / Hinge / Lunge)

# "Leg Push" and "Leg Pull" are too vague. We need to define *how* the leg moves.

# * **`Squat` (Knee Dominant)**: The primary joint action is knee flexion/extension.
# * *Why:* Targets Quads and Glutes.
# * *Examples:* Back Squat, Leg Press, Goblet Squat.


# * **`Hinge` (Hip Dominant)**: The primary joint action is hip flexion/extension.
# * *Why:* Targets Hamstrings, Glutes, Lower Back.
# * *Examples:* Deadlift, RDL (Romanian Deadlift), Hip Thrust, Kettlebell Swing.


# * **`Lunge` (Unilateral)**: Single-leg movements.
# * *Why:* Critical for stability and fixing muscle imbalances.
# * *Examples:* Walking Lunges, Bulgarian Split Squat, Step-ups.


# #### 3. Core: Stability vs. Dynamics

# * **`Static`**: Anti-movement (resisting gravity/force).
# * *Examples:* Plank, Pallof Press.


# * **`Dynamic`**: Flexion or Rotation (moving the spine).
# * *Examples:* Crunches, Russian Twists, Woodchoppers.


# ### Why this is better for your AI

# By using this specific vocabulary, you can program simple, unbreakable rules for the AI Agent:

# **Rule:** *"A Complete Leg Day must contain:"*

# 1. One **Squat** Pattern (e.g., Barbell Squat).
# 2. One **Hinge** Pattern (e.g., RDL).
# 3. One **Lunge** Pattern (e.g., Split Squat).

# If you only used "Push/Pull", the AI wouldn't know if it had covered both the knees and the hips.