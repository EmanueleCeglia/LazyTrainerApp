from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from src.crew.tools import ExerciseRetrieverTool
from textwrap import dedent

class WorkoutModifier:
    def __init__(self, request_data, user_profile_equipment):
        self.data = request_data
        self.equipment = user_profile_equipment 
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
        self.tool = ExerciseRetrieverTool()

    def find_substitute(self):
        # 1. Define the Specialist
        selector = Agent(
            role='Exercise Replacement Specialist',
            goal='Find the best substitute exercise respecting user constraints.',
            backstory="You are an expert coach. You can regression/progress exercises or completely change the focus if asked.",
            verbose=True,
            tools=[self.tool],
            llm=self.llm,
            allow_delegation=False
        )

        # 2. Build Instructions
        
        # A. Equipment & Style Logic
        equipment_instruction = f"User has access to: {self.equipment}."
        if self.data.swap_preference == "Bodyweight Only":
            equipment_instruction += """
            **CRITICAL OVERRIDE:** The user explicitly wants a 'Calisthenics/Bodyweight' STYLE exercise.
            - You MAY select exercises that require a 'Pull-up Bar' or 'Dip Station' **IF AND ONLY IF** they appear in the user's access list above.
            - If the list is empty, strictly select 'Bodyweight' (Floor/No Equipment) exercises.
            """
        elif self.data.swap_preference == "Machine":
             equipment_instruction += " **CRITICAL OVERRIDE:** Prioritize MACHINE-based exercises."

        # B. Strategy Logic (The Decision Tree)
        
        if self.data.target_exercise_name:
            # Case 1: Specific Name (Highest Priority)
            strategy_text = f"""
            The user explicitly requested: '{self.data.target_exercise_name}'.
            1. Search for '{self.data.target_exercise_name}'.
            2. Check equipment (be lenient if they asked for it specifically).
            3. Return the JSON.
            """
            
        elif self.data.new_target_zone or self.data.new_force_type:
            # Case 2: Functional Change
            
            strategy_text = f"""
            The user wants to CHANGE the focus.
            **NEW GOAL:** Find an exercise matching:
            - Target Zone: {self.data.new_target_zone if self.data.new_target_zone else 'Any'}
            - Force Type: {self.data.new_force_type if self.data.new_force_type else 'Any'}
            
            **TOOL INSTRUCTION:** Use the 'Exercise Knowledge Base' tool. 
            Pass '{self.data.new_target_zone}' into the 'target_zone' argument.
            Pass '{self.data.new_force_type}' into the 'force_type' argument.
            """

        # 3. Define Task
        task = Task(
            description=dedent(f"""
                **Goal:** Provide a replacement exercise JSON.
                
                **Context:**
                - User ID: {self.data.user_id}
                - {equipment_instruction}
                
                **Strategy:**
                {strategy_text}
                
                **Output Rules:**
                - Return ONLY valid JSON.
                - Format: {{ "name": "Exact Database Name", "sets": "3", "reps": "8-12", "notes": "Reason for selection..." }}
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