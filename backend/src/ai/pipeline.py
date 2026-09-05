import os
import json
import random
from openai import OpenAI

from src.config import OPENAI_MODEL_NAME

class WorkoutPipeline:
    def __init__(self, user_profile=None, equipment=None, force_split=None, exercise_pool=None):
        self.user_profile = user_profile or {}
        self.equipment = equipment or []
        self.force_split = force_split
        self.exercise_pool = exercise_pool or [] # List of exercise dictionary objects from our DB
        self.client = OpenAI()
        
        # Load exercises from JSON
        json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'exercises.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            self.all_exercises = json.load(f)

    def _normalize_equipment(self, equipment_list):
        eq = [str(item).strip().title() for item in equipment_list if item]
        if "Bodyweight" not in eq:
            eq.append("Bodyweight")
        return eq

    def filter_exercises(self, target_zones=None, force_types=None, equipment=None, avoid_names=None, limit=5):
        zones = [z.title() for z in target_zones] if target_zones else []
        forces = [f.title() for f in force_types] if force_types else []
        avoids = [n.lower() for n in avoid_names] if avoid_names else []
        eq_list = self._normalize_equipment(equipment or self.equipment)
        
        results = []
        for ex in self.all_exercises:
            if avoids and ex.get("name", "").lower() in avoids:
                continue
            if zones and ex.get("target_zone") not in zones:
                continue
            if forces and ex.get("force_type") not in forces:
                continue
            
            ex_equip = [eq.lower() for eq in ex.get("equipment", [])]
            eq_list_lower = [eq.lower() for eq in eq_list]
            # For pure JSON, we want to make sure ALL required equipment is available
            if not all(eq in eq_list_lower for eq in ex_equip):
                continue
                
            results.append(ex)
        
        # Sort: Compound first, then Isolation. Shuffle within each group for variety.
        compounds = [ex for ex in results if ex.get("mechanics") == "Compound"]
        isolations = [ex for ex in results if ex.get("mechanics") != "Compound"]
        random.shuffle(compounds)
        random.shuffle(isolations)
        results = compounds + isolations
        
        return results[:limit]

    def find_equipment_alternatives(self, exercise_name, equipment=None):
        """
        Mode 1: Find exercises with the SAME muscle_group but DIFFERENT equipment.
        Returns a list of alternatives (deterministic, no AI).
        """
        eq_list = self._normalize_equipment(equipment or self.equipment)
        
        # Find the original exercise in the catalog
        original = None
        for ex in self.all_exercises:
            if ex["name"].lower() == exercise_name.lower():
                original = ex
                break
        
        # Fallback: substring match if exact match fails (e.g. LLM reworded the name)
        if not original:
            for ex in self.all_exercises:
                if exercise_name.lower() in ex["name"].lower() or ex["name"].lower() in exercise_name.lower():
                    # For safety, require at least a 4-character overlap to avoid matching "Row" to "Machine Row" randomly
                    if len(exercise_name) > 4:
                        original = ex
                        break
        
        if not original:
            return []
        
        muscle = original.get("muscle_group", "")
        target_zone = original.get("target_zone", "")
        
        alternatives = []
        for ex in self.all_exercises:
            # Same muscle group and target zone
            if ex.get("muscle_group") != muscle or ex.get("target_zone") != target_zone:
                continue
            # Different exercise (not the same one)
            if ex["name"].lower() == exercise_name.lower():
                continue
            # Must have available equipment
            ex_equip = [eq.lower() for eq in ex.get("equipment", [])]
            eq_list_lower = [eq.lower() for eq in eq_list]
            if not all(eq in eq_list_lower for eq in ex_equip):
                continue
            
            alternatives.append(ex)
        
        # Sort: Compound first
        compounds = [ex for ex in alternatives if ex.get("mechanics") == "Compound"]
        isolations = [ex for ex in alternatives if ex.get("mechanics") != "Compound"]
        return compounds + isolations

    def find_smart_replacement(self, exercise_name, target_zone_override, day_exercises, user_goals, equipment=None):
        """
        Mode 2: AI-powered replacement. Finds the best exercise for a given target_zone
        considering what muscles are already covered in the day (gap analysis).
        """
        eq_list = self._normalize_equipment(equipment or self.equipment)
        
        # Get all available exercises in the requested target_zone
        candidates = []
        for ex in self.all_exercises:
            if ex.get("target_zone", "").lower() != target_zone_override.lower():
                continue
            if ex["name"].lower() == exercise_name.lower():
                continue
            ex_equip = [eq.lower() for eq in ex.get("equipment", [])]
            eq_list_lower = [eq.lower() for eq in eq_list]
            if not all(eq in eq_list_lower for eq in ex_equip):
                continue
            candidates.append({"name": ex["name"], "muscle_group": ex.get("muscle_group"), "mechanics": ex.get("mechanics")})
        
        if not candidates:
            return None
        
        # Use AI to pick the best one
        prompt = f"""
        You are an expert fitness coach. The user wants to replace an exercise in their workout day.
        
        Current exercise being replaced: "{exercise_name}"
        Target zone requested: "{target_zone_override}"
        User goals: {json.dumps(user_goals)}
        
        Other exercises ALREADY in this day (avoid muscle overlap):
        {json.dumps(day_exercises)}
        
        Available candidates to choose from:
        {json.dumps(candidates)}
        
        Analyze which muscles are already covered by the existing exercises, identify any GAPS, 
        and pick the BEST candidate that complements the day.
        Also assign the sets, reps, rest, method, intensity, and notes.
        
        Output ONLY valid JSON:
        {{
            "name": "Selected Exercise Name",
            "reason": "Brief explanation of why this was chosen",
            "sets": "4",
            "reps": "8-10",
            "rest": "90s",
            "method": "Standard",
            "intensity": "RPE 7-8",
            "notes": "..."
        }}
        """
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}]
        )
        return json.loads(response.choices[0].message.content)

    def generate_plan(self):
        # Read Rulebooks
        strat_path = os.path.join(os.path.dirname(__file__), 'strategist_rules.md')
        coach_path = os.path.join(os.path.dirname(__file__), 'coach_rules.md')
        try:
            with open(strat_path, 'r', encoding='utf-8') as f:
                strat_rules = f.read()
            with open(coach_path, 'r', encoding='utf-8') as f:
                coach_rules = f.read()
        except FileNotFoundError:
            strat_rules = "No custom rules found. Use standard fitness knowledge."
            coach_rules = "No custom rules found."

        # STEP 1: STRATEGIST
        strategist_prompt = f"""
        You are a master fitness strategist. Create a weekly skeleton based on this user profile.
        User Profile: {json.dumps(self.user_profile)}
        
        CRITICAL RULEBOOK:
        {strat_rules}
        
        {f"CRITICAL OVERRIDE: The user has EXPLICITLY requested to change their split to '{self.force_split}'. You MUST disregard any potential conflicts in the rulebook (such as the Master Split Matrix constraints based on days or experience level) and strictly fulfill this new split request. Best address this new need while still utilizing the rest of the available user information." if self.force_split else ""}
        
        Based ONLY on the rules above and the user's profile, design the weekly split.
        
        Output ONLY valid JSON.
        Format:
        {{
            "plan_name": "...",
            "schedule": {{
                "Week 1": {{
                    "Day 1": {{
                        "focus_zones": ["Upper", "Lower", "Core"],
                        "focus_forces": ["Push", "Pull", "Squat", "Hinge", "Lunge", "Dynamic", "Static"],
                        "num_exercises": 5,
                        "method": "Pure Strength | Muscle Growth | Muscle Endurance"
                    }},
                    "Day 2": "Rest"
                }}
            }}
        }}
        The schedule MUST match the days_per_week in the user profile (e.g. 4 days means 4 Days with exercises, the rest "Rest").
        Assign the correct "method" to each day based on the Goal-to-Method Mapping in the rulebook.
        NAMING RULE: The "plan_name" MUST follow this exact format: "The [Funny Adjective related to user goals] [Random Animal] Program". Examples: "The Super Strong Beaver Program", "The Shredded Flamingo Program", "The Explosive Gorilla Program". Always start with "The" and end with "Program". Be creative and humorous!
        """
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": strategist_prompt}]
        )
        skeleton = json.loads(response.choices[0].message.content)

        # STEP 2: SELECTOR (Pure Python)
        selected_schedule = {}
        schedule = skeleton.get("schedule", {}).get("Week 1", {})
        
        for day, details in schedule.items():
            if details == "Rest" or not isinstance(details, dict):
                selected_schedule[day] = "Rest"
                continue
                
            zones = details.get("focus_zones", [])
            forces = details.get("focus_forces", [])
            num_ex = details.get("num_exercises", 5)
            
            # First, try to pull from the exercise_pool (preservation of old exercises)
            exercises = []
            if self.exercise_pool:
                # Find matching exercises in pool
                pool_matches = [
                    ex for ex in self.exercise_pool 
                    if (not zones or ex.get("target_zone") in zones) and (not forces or ex.get("force_type") in forces)
                ]
                random.shuffle(pool_matches)
                selected_from_pool = pool_matches[:num_ex]
                exercises.extend(selected_from_pool)
                
                # Remove them from the pool so they aren't repeated
                for used in selected_from_pool:
                    self.exercise_pool.remove(used)
                    
            # If we don't have enough from the pool, get new ones
            if len(exercises) < num_ex:
                more = self.filter_exercises(target_zones=zones, force_types=forces, limit=num_ex - len(exercises))
                exercises.extend(more)
            
            # If we don't have enough, try without forces
            if len(exercises) < num_ex:
                more = self.filter_exercises(target_zones=zones, force_types=[], limit=num_ex - len(exercises))
                exercises.extend(more)
            
            # Deduplicate
            unique_ex = []
            seen = set()
            for ex in exercises:
                if ex["name"] not in seen:
                    unique_ex.append(ex)
                    seen.add(ex["name"])
                    
            selected_schedule[day] = {
                "method": details.get("method", "Standard Training"),
                "exercises": unique_ex
            }

        # STEP 3: COACH
        coach_prompt = f"""
        You are an expert fitness coach. Given the selected exercises for each day, assign sets, reps, rest, intensity, and specific methods based on the user's goals AND the day's assigned method.
        User Goals: {self.user_profile.get('goals', [])}
        Selected Exercises & Assigned Methods: {json.dumps(selected_schedule)}
        
        IMPORTANT: Each exercise object contains a "mechanics" field ("Compound" or "Isolation") and a "force_type" field. You must strictly REORDER the exercises provided to you using the 5-Tier Master Sequencing Hierarchy found in the coaching rules below. Do not just use the order provided in the input.
        
        COACHING RULES:
        {coach_rules}
        
        Output ONLY valid JSON matching this exact structure:
        {{
            "plan_name": "{skeleton.get('plan_name', 'Custom Plan')}",
            "Week 1": {{
                "Day 1": {{
                    "exercises": [
                        {{
                            "name": "Exercise Name",
                            "sets": "e.g., 5 or 3",
                            "reps": "e.g., 5 or 12",
                            "rest": "e.g., 120s or 60s",
                            "method": "Pure Strength | Muscle Growth | Muscle Endurance",
                            "intensity": "e.g., RPE 8-9, RPE 7-8, RPE 6-7",
                            "notes": "..."
                        }}
                    ]
                }},
                "Day 2": "Rest"
            }}
        }}
        Ensure every exercise from the input is included. Keep the Day keys exactly as provided.
        CRITICAL RULE: NEVER alter the `name` of the exercises provided in the input. Keep them exactly as written.
        """
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": coach_prompt}]
        )
        final_plan = json.loads(response.choices[0].message.content)
        
        # Merge plan_name outside of schedule structure if necessary
        # The frontend/routes expect schedule to be plan_json
        # So we just return final_plan
        return final_plan

class WorkoutModifier:
    def __init__(self, request_data, user_profile_equipment):
        self.data = request_data
        self.equipment = user_profile_equipment 
        self.client = OpenAI()
        self.pipeline = WorkoutPipeline(equipment=self.equipment)
        
    def find_substitute(self):
        # 1. Use pure Python to find a substitute
        if self.data.target_exercise_name:
            candidates = [ex for ex in self.pipeline.all_exercises if ex["name"].lower() == self.data.target_exercise_name.lower()]
        else:
            tgt_zone = [self.data.new_target_zone] if self.data.new_target_zone else []
            tgt_force = [self.data.new_force_type] if self.data.new_force_type else []
            candidates = self.pipeline.filter_exercises(target_zones=tgt_zone, force_types=tgt_force, limit=5)
            
            # If empty, broaden search
            if not candidates:
                candidates = self.pipeline.filter_exercises(target_zones=tgt_zone, force_types=[], limit=5)
                
        if not candidates:
            return {"error": "No substitute found."}
            
        selected = candidates[0]
        
        # 2. Use LLM to assign sets/reps for the substitute
        prompt = f"""
        You are a coach. The user swapped an exercise. Assign sets and reps for this new exercise.
        New Exercise: {selected['name']}
        Instructions: {selected.get('instructions', '')}
        
        Output ONLY valid JSON:
        {{
            "name": "{selected['name']}",
            "sets": "3",
            "reps": "8-12",
            "rest": "60s",
            "method": "Standard",
            "intensity": "RPE 7",
            "notes": "..."
        }}
        """
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}]
        )
        return json.loads(response.choices[0].message.content)

    def adjust_difficulty(self, current_exercises: list):
        prompt = f"""
        You are an adaptive performance coach. Adjust the difficulty of these exercises based on user feedback.
        Feedback: {self.data.user_feedback or self.data.modification_type}
        New Method: {self.data.new_method or 'Scale volume/intensity'}
        
        Current Exercises: {json.dumps(current_exercises)}
        
        Output ONLY a JSON object containing a list called "exercises" with the updated parameters (do NOT change the names).
        {{
            "exercises": [
                {{
                    "name": "...",
                    "sets": "...",
                    "reps": "...",
                    "rest": "...",
                    "method": "...",
                    "intensity": "...",
                    "notes": "..."
                }}
            ]
        }}
        """
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}]
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("exercises", [])

class BulkExerciseSwapper:
    """
    Agent that handles bulk exercise replacement.
    Given a list of exercises to swap (across multiple days), it:
    1. Finds alternatives from the JSON catalog matching target_zone & force_type
    2. Excludes exercises already in the plan to avoid duplicates
    3. Uses the LLM to assign coherent sets/reps based on the full program context
    """
    def __init__(self, equipment, plan_schedule, user_goals):
        self.client = OpenAI()
        self.pipeline = WorkoutPipeline(equipment=equipment)
        self.plan_schedule = plan_schedule  # Full current schedule
        self.user_goals = user_goals
        
    def _get_all_plan_exercise_names(self):
        """Extract every exercise name currently in the plan."""
        names = set()
        for week in self.plan_schedule.values():
            if isinstance(week, dict):
                for day_data in week.values():
                    if isinstance(day_data, dict):
                        for ex in day_data.get("exercises", []):
                            names.add(ex.get("name", "").lower())
        return names

    def _find_exercise_in_catalog(self, name):
        """Look up the full exercise dict from the JSON catalog by name."""
        for ex in self.pipeline.all_exercises:
            if ex["name"].lower() == name.lower():
                return ex
        return None
    
    def find_alternatives(self, exercises_to_swap):
        """
        exercises_to_swap: list of {"day_name": str, "exercise_name": str}
        Returns: {"replacements": [...], "failures": [...]}
        """
        existing_names = self._get_all_plan_exercise_names()
        replacements = []
        failures = []
        
        for item in exercises_to_swap:
            day_name = item["day_name"]
            ex_name = item["exercise_name"]
            
            # 1. Look up the original exercise in our catalog
            original = self._find_exercise_in_catalog(ex_name)
            
            if not original:
                # Exercise not in catalog (maybe LLM-generated name). Try broader search.
                # Get the exercise from the plan to see its context
                original = {"target_zone": "", "force_type": "", "equipment": []}
            
            target_zones = [original.get("target_zone")] if original.get("target_zone") else []
            force_types = [original.get("force_type")] if original.get("force_type") else []
            
            # 2. Find candidates from catalog
            candidates = self.pipeline.filter_exercises(
                target_zones=target_zones,
                force_types=force_types,
                limit=10
            )
            
            # 3. Filter out exercises already in the plan AND the ones we're swapping in this batch
            new_names_so_far = {r["new_exercise"]["name"].lower() for r in replacements}
            candidates = [
                c for c in candidates
                if c["name"].lower() != ex_name.lower()
                and c["name"].lower() not in existing_names
                and c["name"].lower() not in new_names_so_far
            ]
            
            # 4. If strict match fails, broaden: same zone, any force type
            if not candidates:
                candidates = self.pipeline.filter_exercises(
                    target_zones=target_zones,
                    force_types=[],
                    limit=10
                )
                candidates = [
                    c for c in candidates
                    if c["name"].lower() != ex_name.lower()
                    and c["name"].lower() not in existing_names
                    and c["name"].lower() not in new_names_so_far
                ]
            
            if not candidates:
                failures.append({
                    "day_name": day_name,
                    "exercise_name": ex_name,
                    "reason": f"No alternative found for '{ex_name}' with matching target zone."
                })
                continue
            
            # Pick the first candidate
            selected = candidates[0]
            replacements.append({
                "day_name": day_name,
                "original_name": ex_name,
                "new_exercise": selected
            })
        
        if not replacements:
            return {"replacements": [], "failures": failures}
        
        # 5. Use LLM to assign coherent sets/reps for ALL replacements at once
        replacement_summary = []
        for r in replacements:
            replacement_summary.append({
                "day_name": r["day_name"],
                "original_name": r["original_name"],
                "new_name": r["new_exercise"]["name"],
                "target_zone": r["new_exercise"].get("target_zone", ""),
                "force_type": r["new_exercise"].get("force_type", ""),
            })
        
        prompt = f"""
        You are an expert fitness coach. The user has requested to swap several exercises in their training program.
        
        User Goals: {json.dumps(self.user_goals)}
        Current Full Program: {json.dumps(self.plan_schedule)}
        
        Exercises being replaced:
        {json.dumps(replacement_summary)}
        
        For EACH new exercise, assign sets, reps, rest, method, intensity, and notes that:
        1. Are coherent with the REST of the exercises on that same day
        2. Match the user's goals
        3. Replace the old exercise seamlessly
        
        Output ONLY valid JSON:
        {{
            "exercises": [
                {{
                    "day_name": "Day 1",
                    "name": "New Exercise Name",
                    "sets": "4",
                    "reps": "8-10",
                    "rest": "90s",
                    "method": "Standard",
                    "intensity": "RPE 7-8",
                    "notes": "Replaces Old Exercise"
                }}
            ]
        }}
        """
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}]
        )
        coached = json.loads(response.choices[0].message.content)
        coached_list = coached.get("exercises", [])
        
        # Merge coached data back into replacements
        final_replacements = []
        for r in replacements:
            # Find the matching coached exercise
            coached_match = next(
                (c for c in coached_list if c.get("name", "").lower() == r["new_exercise"]["name"].lower()),
                None
            )
            if coached_match:
                final_replacements.append({
                    "day_name": r["day_name"],
                    "original_name": r["original_name"],
                    "new_exercise": coached_match
                })
            else:
                # Fallback: use the raw exercise with default params
                final_replacements.append({
                    "day_name": r["day_name"],
                    "original_name": r["original_name"],
                    "new_exercise": {
                        "name": r["new_exercise"]["name"],
                        "sets": "3",
                        "reps": "10",
                        "rest": "60s",
                        "method": "Standard",
                        "intensity": "RPE 7",
                        "notes": f"Replaces {r['original_name']}"
                    }
                })
        
        return {"replacements": final_replacements, "failures": failures}

