from crewai import Task
from textwrap import dedent

class WorkoutTasks:
    
    # 1. THE STRATEGY (The Architect)
    # Focus: Splits, Volume, Frequency. No specific exercise names yet.
    def strategy_task(self, agent, user_profile):
        return Task(
            description=dedent(f"""
                **Analyze the User Profile:**
                - Days available: {user_profile['days_per_week']}
                - Split Preference: {user_profile['split_type']} (Strictly adhere to this)
                - Goal: {user_profile['goals']}
                - Experience: {user_profile['experience_level']}
                - Target Zones: {user_profile['target_zone']}

                **Your Job:**
                Create a Weekly Split Skeleton.
                1. Define the focus for each day (e.g., "Day 1: Upper Body Push", "Day 2: Lower Body").
                2. List the **Movement Patterns** required (e.g., "Horizontal Push", "Vertical Pull", "Squat Pattern").
                3. Do NOT pick specific exercises (like "Barbell Bench Press"). Just write "Compound Chest Press".
                
                **Example Output format:**
                Day 1 (Upper Push): Chest Compound, Shoulder Isolation, Tricep Isolation.
                Day 2 (Lower): Quad Compound, Hinge Compound, Calf Isolation.
            """),
            expected_output="A high-level weekly training split with movement patterns defined for each day.",
            agent=agent
        )

    # 2. THE SELECTION (The Headhunter)
    # Focus: Querying the DB and filling the slots.
    def selection_task(self, agent, user_profile):
        return Task(
            description=dedent(f"""
                **Context:**
                Take the 'Weekly Split Skeleton' provided by the Strategist.
                
                **Constraints:**
                - Location: {user_profile['location']}
                - Equipment: {user_profile['equipment']} (Use this list STRICTLY)
                - Injuries: {user_profile['injuries']}
                
                **Your Job:**
                For every 'Movement Pattern' listed in the skeleton, search the database using your Tool.
                
                **Rules:**
                1. **STRICT DB LOOKUP:** You MUST use the 'Exercise Knowledge Base' tool for every single slot.
                2. **No Hallucinations:** If the tool says "No results", try a broader term (e.g., change "Incline Dumbbell Press" to "Push").
                3. **Replacement:** Replace abstract patterns ("Chest Compound") with REAL names found ("Dumbbell Bench Press").
                4. **Filter:** Ensure the selected exercise actually exists in the tool's output.
            """),
            expected_output="The detailed list of actual exercises selected from the database for each day.",
            agent=agent
        )

    # 3. THE COACHING (The Scientist)
    # Focus: Math (Sets/Reps) and JSON Formatting.
    def coaching_task(self, agent, user_profile):
        return Task(
            description=dedent(f"""
                **Context:**
                You have the list of exercises. Now apply the Training Principles.
                
                **User Goal:** {user_profile['goals']}
                **Experience:** {user_profile['experience_level']}

                **Your Job:**
                1. Assign Sets, Reps, Rest (Seconds), and RPE.
                   - Hypertrophy: 3-4 sets, 8-12 reps, 60-90s rest.
                   - Strength: 5 sets, 3-5 reps, 120-180s rest.
                   - Endurance: 2-3 sets, 15+ reps, 30-60s rest.
                
                2. **FORMATTING (CRITICAL):**
                You must output a **Single, Valid JSON Object**. 
                - Do NOT wrap it in markdown code blocks (like ```json ... ```).
                - Do NOT add introductory text ("Here is your plan").
                - Just the raw JSON string.
                
                **Required JSON Structure:**
                {{
                  "plan_name": "Name of the program",
                  "week_1": {{
                    "Day 1": {{
                        "focus": "Upper Body / Push / etc",
                        "exercises": [
                            {{ 
                                "name": "Exact Name from Step 2", 
                                "sets": 3, 
                                "reps": "8-12", 
                                "rest": 90, 
                                "notes": "Focus on eccentric..." 
                            }}
                        ]
                    }},
                    "Day 2": {{ ... }}
                  }}
                }}
            """),
            expected_output="A valid, raw JSON string containing the full workout program. No Markdown.",
            agent=agent
        )