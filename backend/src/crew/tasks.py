from crewai import Task
from textwrap import dedent

class WorkoutTasks:
    def design_plan_task(self, agent, user_profile):
        return Task(
            description=dedent(f"""
                **Analyze the User Profile:**
                - Split Strategy: {user_profile['split_type']} (CRITICAL)
                - Days per Week: {user_profile['days_per_week']}
                - Location: {user_profile['location']}
                - Equipment: {user_profile['equipment']}
                - Injuries: {user_profile['injuries']}
                - Experience: {user_profile['experience_level']}
                - Target Zones: {user_profile['target_zone']}

                **Your Mission:**
                1. Design a {user_profile['days_per_week']}-day training split strictly following the '{user_profile['split_type']}' strategy.
                   - If 'Monofrequency': Focus on one main muscle group per day (e.g., Chest Mon, Back Tue).
                   - If 'Multifrequency': Use Upper/Lower or Full Body splits.
                
                2. **CRITICAL: EXERCISE VERIFICATION**
                   - For EVERY exercise you want to assign, you MUST use the 'Exercise Knowledge Base' tool.
                   - Search for exercises that match the specific muscle group (e.g., 'Chest Compound', 'Back Isolation').
                   - You must ONLY assign exercises that the Tool returns. Do not invent exercise names.
                   - If the tool returns no results for a specific query, try a broader query (e.g., 'Push' instead of 'Incline Bench').
                
                3. Safety First:
                   - The Tool will automatically filter out unsafe exercises for {user_profile['injuries']}. 
                   - Trust the tool's output regarding safety.
            """),
            expected_output=dedent("""
                A detailed Markdown training plan.
                Structure:
                ## Day 1: [Focus]
                - [Exercise Name] | [Sets] x [Reps] | [Rest]
                ...
                
                ## Day 2: [Focus]
                ...
            """),
            agent=agent
        )