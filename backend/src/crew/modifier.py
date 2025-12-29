from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from src.crew.tools import ExerciseRetrieverTool
from textwrap import dedent

class WorkoutModifier:
    def __init__(self, request_data):
        self.data = request_data
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
        self.tool = ExerciseRetrieverTool()

    def find_substitute(self):
        # 1. Define the Specialist
        selector = Agent(
            role='Exercise Replacement Specialist',
            goal='Find the best biomechanical substitute for a specific exercise.',
            backstory="You are an expert at regression and progression of exercises. You find alternatives that target the same muscle group.",
            verbose=True,
            tools=[self.tool],
            llm=self.llm,
            allow_delegation=False
        )

        # 2. Define the Task
        task = Task(
            description=dedent(f"""
                **Goal:** Find a substitute for '{self.data.current_exercise_name}'.
                
                **Context:**
                - User Equipment: {self.data.available_equipment} (Assume 'Bodyweight' is always available)
                - Injuries: {self.data.injuries}
                
                **Process:**
                1. **Analyze Biomechanics:** - What represents '{self.data.current_exercise_name}'? (e.g., Lat Pulldown = Vertical Pull).
                2. **Search Strategy:** - Use the tool to search for that PATTERN (e.g. search "Vertical Pull" or "Back").
                   - Do NOT search for the specific exercise name "Lat Pulldown" because you already know the user can't do it.
                3. **Selection:**
                   - Pick the best match from the tool's output.
                   - If user has 'Pull-up Bar', look specifically for 'Pull Up' or 'Chin Up'.
                
                **Output Rules:**
                - Return ONLY valid JSON.
                - If no exercise is found, return {{ "error": "No suitable exercise found" }}.
                - Format: {{ "name": "Exact Database Name", "sets": "...", "reps": "...", "notes": "..." }}
            """),
            expected_output="A JSON object containing the new exercise details.",
            agent=selector
        )

        # 3. Run
        crew = Crew(
            agents=[selector],
            tasks=[task],
            verbose=True
        )
        
        return crew.kickoff()
    
    def adjust_difficulty(self, current_exercises: list):
        # 1. Define the Coach (The Scientist)
        coach = Agent(
            role='Adaptive Performance Coach',
            goal='Adjust training variables (Sets, Reps, Methods) based on user feedback.',
            backstory="You are an expert in periodization. You take an existing workout and scale it up/down or change the methodology (e.g., from Standard to EMOM) without changing the exercises themselves.",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )

        # 2. Construct the Instruction based on user intent
        if self.data.modification_type == "method":
            method_text = f"Change the training method to: {self.data.new_method}" if self.data.new_method else "Select a different, appropriate training method (e.g. Supersets, Circuit, EMOM) to spice things up."
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