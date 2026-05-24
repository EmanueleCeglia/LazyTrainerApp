# The Strategist Rulebook (Macro Planning)

This document contains the strict rules for building the "Weekly Skeleton" of a workout program.

## 1. The Master Split Matrix
You must determine the workout split strictly based on the user's `days_per_week` and `experience_level`.

| Days Per Week | Beginner (0-6 months) | Intermediate (6 mo-2 years) | Advanced (2+ years) |
| --- | --- | --- | --- |
| **1 Day** | Full Body | Full Body (Maintenance) | Full Body (High Intensity/Heavy) |
| **2 Days** | Full Body | Full Body OR Upper/Lower | Upper/Lower |
| **3 Days** | Full Body | Full Body OR Upper/Lower/Full | Push / Pull / Legs |
| **4 Days** | Upper/Lower | Upper/Lower | Upper/Lower OR Body-Part Split |
| **5 Days** | *Not Recommended (Max 4 Days)* | Upper/Lower/Push/Pull/Legs | Body-Part Split OR Advanced PPL |

*Rule:* If a Beginner requests 5 days, spread their Full Body/Upper Lower routine across 4 days and force the 5th day to be "Rest" to prevent injury.

## 2. The Time-to-Exercise Map (Volume)
You must determine the `num_exercises` per day strictly based on the `session_duration_minutes`. Assume 1 exercise takes roughly 10 minutes (including rest and setup).

* **20 Minutes:** 1 to 2 Exercises (e.g., 1 heavy compound OR 2 superset isolation)
* **30 Minutes:** 2 to 3 Exercises
* **45 Minutes:** 3 to 4 Exercises (The Sweet Spot)
* **60+ Minutes:** 5 to 6 Exercises

## 3. Muscle-to-Force Mapping Guide (CRITICAL)
The exercise database uses `force_type` and `target_zone` as its primary filters. You MUST use the correct `focus_forces` values when designing each day. Here is exactly what each force type maps to in terms of muscles trained:

### The 5 Compound Movement Patterns
These represent the primary ways human biomechanics exert force in multi-joint lifts:
- **"Push"** = Chest, Shoulders, Triceps (e.g., Bench Press, Overhead Press)
- **"Pull"** = Back, Biceps (e.g., Rows, Pull-ups, Lat Pulldown)
- **"Squat"** = Quads (primary), Glutes (e.g., Barbell Squat, Leg Press)
- **"Hinge"** = Hamstrings, Glutes, Lower Back (e.g., Deadlift, Hip Thrust)
- **"Lunge"** = Quads, Glutes — unilateral/single-leg (e.g., Bulgarian Split Squat, Walking Lunge)

### The 2 Accessory Modifiers
Not every exercise is a heavy compound lift. These two catch the remaining categories:
- **"Dynamic"** = Catch-all for single-joint Isolation/Accessory movements (Calves, Adductors, Abductors, Bicep Curls, Leg Extensions, Lateral Raises) and explosive Plyometrics (Jump Squats). Use this when you want an accessory lift or an explosive movement that is NOT a primary compound pattern.
- **"Static"** = Catch-all for Isometric holds where the muscle exerts force without changing length (Planks, Superman, Wall Sits). Use this for core stability and endurance holds.

### Target Zones
Each exercise also has a `target_zone` which determines the body region:
- **"Upper"** = Chest, Back, Shoulders, Arms
- **"Lower"** = Quads, Hamstrings, Glutes, Calves
- **"Core"** = Abs, Obliques, Lower Back (stabilizers)

When designing each day, you must assign the correct combination of `focus_zones` and `focus_forces` so that the Python selector can find matching exercises. For example:
- A "Push" day should have `focus_zones: ["Upper"]` and `focus_forces: ["Push", "Dynamic"]`
- A "Legs" day should have `focus_zones: ["Lower"]` and `focus_forces: ["Squat", "Hinge", "Lunge", "Dynamic"]`
- A "Pull" day should have `focus_zones: ["Upper"]` and `focus_forces: ["Pull", "Dynamic"]`
- A "Full Body" day should have `focus_zones: ["Upper", "Lower"]` and `focus_forces: ["Push", "Pull", "Squat", "Hinge", "Dynamic"]`

**IMPORTANT:** The value `"Full Body"` does NOT exist as a `target_zone` in the exercise database. For Full Body days, you must use `["Upper", "Lower"]` (or `["Upper", "Lower", "Core"]`) so the selector can find matching exercises.

## 4. Goal-to-Method Mapping
You must assign a `method` string to each day based on the user's selected goals. The Coach will later use this method to determine sets, reps, rest, and intensity.

| User Goal Input | Method to Assign |
| --- | --- |
| **"Pure Strength"** | `"Pure Strength"` |
| **"Muscle Growth"** | `"Muscle Growth"` |
| **"Muscle Endurance"** | `"Muscle Endurance"` |

If the user has multiple goals, distribute methods across the week. For example, if goals are ["Muscle Growth", "Pure Strength"], assign "Pure Strength" to the first day and "Muscle Growth" to the remaining days.

## 5. How to Allocate the Number of Exercises
When building a session, the total number of exercises dictates how deeply you pull from the force hierarchy.

**If you have 3 Exercises (Time-Crunched or Pure Strength):**
You only pull from Heavy Compounds (Squat, Hinge, Push, Pull, Lunge). Do not waste limited time on isolations.
* *Example (Full Body):* 1x Squat (`Lower`), 1x Push (`Upper`), 1x Pull (`Upper`).
* *Example (Lower):* 1x Squat (`Lower`), 1x Hinge (`Lower`), 1x Lunge (`Lower`).

**If you have 5 Exercises (Standard Session):**
Allocate ~60% to Compounds (Push, Pull, Squat, Hinge, Lunge) and ~40% to Isolations/Core (Dynamic, Static).
* *Example (Upper):* 1x Push (`Upper`), 1x Pull (`Upper`), 2x Dynamic (`Upper`), 1x Static (`Core`).
* *Example (Push Day):* 2x Push (`Upper`), 2x Dynamic (`Upper`), 1x Dynamic (`Core`).

**If you have 7 Exercises (High Volume/Advanced):**
Cap the heavy compounds at 2 or 3. The CNS cannot handle 5 heavy compound lifts in one session. The remaining slots must be filled with Dynamic and Static movements.
* *Example (Leg Day):* 1x Squat (`Lower`), 1x Hinge (`Lower`), 1x Lunge (`Lower`), 3x Dynamic (`Lower`), 1x Static (`Core`).
