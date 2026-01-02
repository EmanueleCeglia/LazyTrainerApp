from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from src.crew.tools import ExerciseRetrieverTool
from textwrap import dedent

class WorkoutModifier:
    def __init__(self, request_data, user_profile_equipment):
        self.data = request_data
        self.equipment = user_profile_equipment 
        
        # ⚡ OPTIMIZATION 1: Use Mini. 
        # It is smart enough for this task and 30x cheaper.
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) 
        self.tool = ExerciseRetrieverTool()

    def find_substitute(self):
        # 1. Define the Specialist
        selector = Agent(
            role='Exercise Replacement Specialist',
            goal='Find the best substitute exercise efficiently.',
            backstory="You are a precise database operator. You map user requests to strict SQL filters, pick the best match, and return JSON immediately.",
            verbose=True,
            tools=[self.tool],
            llm=self.llm,
            allow_delegation=False,
            max_iter=5 # ⚡ Safety Buffer: Enough retries to fix errors, but Mini makes it cheap.
        )

        # 2. Build the "One-Shot" Strategy
        # We pre-calculate the arguments for the AI so it doesn't have to "think" about them.
        
        # A. Equipment Context
        equipment_instruction = f"User Inventory: {self.equipment}"
        if self.data.swap_preference == "Bodyweight Only":
             equipment_instruction += " (Preference: Bodyweight Style. Use Bars/Dip Stations if in Inventory.)"

        # B. Construct the Search Strategy
        if self.data.target_exercise_name:
            # Case 1: Specific Name
            decision_logic = f"""
            **USER REQUEST:** Specific Exercise -> '{self.data.target_exercise_name}'
            **ACTION:** 1. Call tool with `query='{self.data.target_exercise_name}'`.
            2. Ignore zone/force filters. 
            3. Return the result.
            """
        elif self.data.new_target_zone or self.data.new_force_type:
            # Case 2: Functional Change (The most complex one)
            tgt_zone = self.data.new_target_zone if self.data.new_target_zone else "Do not filter"
            tgt_force = self.data.new_force_type if self.data.new_force_type else "Do not filter"
            
            decision_logic = f"""
            **USER REQUEST:** Functional Swap
            **ACTION:** Call tool with these STRICT arguments:
            - `target_zone`: ['{self.data.new_target_zone}'] (IF '{self.data.new_target_zone}' is not None)
            - `force_type`: ['{self.data.new_force_type}'] (IF '{self.data.new_force_type}' is not None)
            - `query`: "Alternative for {self.data.current_exercise_name}"
            """
        else:
            # Case 3: Standard Swap
            decision_logic = f"""
            **USER REQUEST:** Standard Substitute
            **ACTION:** 1. Call tool with `query='Similar to {self.data.current_exercise_name}'`.
            2. Do NOT apply strict zone/force filters unless necessary.
            """

        # 3. Define the Task
        task = Task(
            description=dedent(f"""
                **Goal:** Find a replacement exercise.
                
                **Context:**
                - {equipment_instruction}
                
                **Decision Logic:**
                {decision_logic}
                
                **Failure Handling:**
                - If the tool returns "No exercises found", REMOVE the `force_type` filter and try again with just `query`.
                - If that fails, remove `target_zone` and search broadly.
                
                **Output Rules:**
                - Return ONLY valid JSON.
                - Format: {{ "name": "Exact Database Name", "sets": "3", "reps": "8-12", "notes": "..." }}
            """),
            expected_output="A valid JSON object.",
            agent=selector
        )

        # 4. Run
        crew = Crew(agents=[selector], tasks=[task], verbose=True)
        return crew.kickoff()
    

    def adjust_difficulty(self, current_exercises: list):
        # 1. Define the Coach (The Scientist)
        coach = Agent(
            role='Adaptive Performance Coach',
            goal='Adjust training variables (Sets, Reps, Methods) based on user feedback.',
            backstory="You are an expert in periodization. You scale workouts up/down without changing the exercises themselves.",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )

        # 2. Construct the Instruction based on user intent
        if self.data.modification_type == "method":
            method_text = f"Change the training method to: {self.data.new_method}" if self.data.new_method else "Select a different, appropriate training method (e.g. Supersets, Circuit, EMOM)."
            instruction = f"User wants a structural change. {method_text}"
        else:
            # Scaling (Volume/Intensity)
            instruction = f"User wants to adjust difficulty. Feedback: '{self.data.user_feedback}'. Adjust Sets/Reps/Rest accordingly."

        # 3. Define the Task
        task = Task(
            description=dedent(f"""
                **Goal:** Modify the parameters of the provided exercises.
                
                **Input Data:**
                {current_exercises}
                
                **Instructions:**
                {instruction}
                
                **Constraints:**
                - KEEP the exercise names exactly as they are. Do not swap exercises.
                - Modify ONLY: sets, reps, rest, and notes.
                - If the method changes (e.g., EMOM), write the details clearly in the 'reps' or 'notes' fields.
                
                **Output:**
                Return a JSON List of the modified exercise objects.
                Format: [ {{ "name": "...", "sets": "...", "reps": "...", "rest": "...", "notes": "..." }}, ... ]
            """),
            expected_output="A JSON List of modified exercises.",
            agent=coach
        )

        # 4. Run
        crew = Crew(
            agents=[coach],
            tasks=[task],
            verbose=True
        )
        
        return crew.kickoff()