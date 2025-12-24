from crewai import Task
from textwrap import dedent

class WorkoutTasks:
    def design_plan_task(self, agent, user_profile):
        return Task(
            description=dedent(f"""
                **Analyze the User Profile:**
                - Goal: {user_profile['goals']}
                - Experience: {user_profile['experience_level']}
                - Injuries: {user_profile['injuries']}
                - Equipment: {user_profile['equipment']}
                - Days available: {user_profile['days_per_week']}

                **Your Mission:**
                1. Design a full {user_profile['days_per_week']}-day workout split (e.g., Upper/Lower, PPL, Full Body).
                2. For EACH exercise in the split, you MUST use the 'Exercise Knowledge Base' tool to verify it exists and fits the user's constraints.
                3. If the user has an injury (e.g., knee_pain), DO NOT search for or assign dangerous exercises (like heavy Squats). Find safe alternatives.
                4. Ensure the program has balanced volume (Push vs Pull).
            """),
            expected_output=dedent("""
                A detailed Markdown training plan.
                Structure:
                ## Day 1: [Focus]
                - [Exercise Name] | [Sets] x [Reps] | [Notes]
                ...
                
                ## Day 2: [Focus]
                ...
            """),
            agent=agent
        )