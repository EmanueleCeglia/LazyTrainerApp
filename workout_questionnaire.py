from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict


class WorkoutQuestionnaire:
    """
    Console-driven questionnaire that collects workout preferences
    and stores the answers in JSON format.
    """

    # --- Static data ------------------------------------------------------ #
    LEVEL_OPTIONS = ["Beginner", "Intermediate", "Advanced"]

    TRAIN_OPTIONS = ["Upper body", "Lower body", "Full body"]

    MUSCLE_MAP = {
        "Upper body": ["Chest", "Lats", "Shoulders", "Biceps", "Triceps"],
        "Lower body": ["Quads", "Hamstrings", "Glutes", "Calves"],
        "Full body": [
            "Chest", "Back", "Shoulders", "Biceps", "Triceps",
            "Quads", "Hamstrings", "Glutes", "Calves",
        ],
    }

    EQUIPMENT_PARK = [
        "Gymnastics rings", "Parallettes", "Barbell",
        "Dumbbells", "Kettlebell",
    ]

    EQUIPMENT_HOME = [
        "Gymnastics rings", "Parallel bars", "Parallettes",
        "Pull-up bar", "Barbell", "Dumbbells", "Kettlebell",
    ]

    # --- Public API ------------------------------------------------------- #
    def run(self) -> Dict:
        """Run the questionnaire and return the collected payload."""
        payload = {
            "level":           self._ask_level(),
            "train_target":    self._ask_train_target(),
            "focus_muscle":    None,   # set later
            "muscles":         [],     # set later
            "duration_minutes": self._prompt_int_range(
                "How much time do you have available (in minutes)?", 45, 180
            ),
            "location":        None,   # set later
            "equipment":       [],     # set later
        }

        # Focus on specific muscles (conditional)
        payload["focus_muscle"] = self._prompt_yes_no(
            "Do you want to put specific focus on certain muscles?"
        )
        if payload["focus_muscle"]:
            payload["muscles"] = self._ask_muscles(payload["train_target"])

        # Training location and equipment (conditional)
        payload["location"], payload["equipment"] = self._ask_location_and_equipment()

        return payload

    def save_payload(self, payload: Dict, file_path: Path | str = "workout_payload.json") -> Path:
        """Save the collected payload to disk and return the absolute path."""
        file_path = Path(file_path)
        with file_path.open("w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)
        return file_path.resolve()

    # --- Helper questions -------------------------------------------------- #
    def _ask_level(self) -> str:
        return self._prompt_choice(
            "What kind of athlete do you think you belong to?", self.LEVEL_OPTIONS
        )

    def _ask_train_target(self) -> str:
        return self._prompt_choice(
            "What do you want to train today?", self.TRAIN_OPTIONS
        )

    def _ask_muscles(self, train_target: str) -> List[str]:
        available = self.MUSCLE_MAP[train_target]
        print("Select the muscle groups (comma-separated):")
        return self._prompt_multi_select(available)

    def _ask_location_and_equipment(self) -> tuple[str, List[str]]:
        location = self._prompt_choice("Where are you training?", ["Gym", "Park", "Home"])
        equipment: List[str] = []

        if location in {"Park", "Home"}:
            has_equipment = self._prompt_yes_no("Do you have any specific equipment available?")
            if location == "Park":
                equipment = (
                    self._prompt_multi_select(self.EQUIPMENT_PARK) if has_equipment
                    else []
                ) + ["Pull-up bar", "Parallel bars", "Ground"]
            elif location == "Home":
                equipment = (
                    self._prompt_multi_select(self.EQUIPMENT_HOME) if has_equipment
                    else []
                ) + ["Ground"]
        return location, equipment

    # --- Generic prompt utilities ----------------------------------------- #
    @staticmethod
    def _prompt_choice(question: str, options: List[str]) -> str:
        """Display a question with enumerated options and return the selected value."""
        print(question)
        for idx, opt in enumerate(options, start=1):
            print(f"  {idx}. {opt}")
        while True:
            choice = input("Select the corresponding number: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(options):
                return options[int(choice) - 1]
            print("Invalid input, please try again.")

    @staticmethod
    def _prompt_yes_no(question: str) -> bool:
        """Return True if the user answers 'y', False if 'n'."""
        while True:
            ans = input(f"{question} [y/n]: ").strip().lower()
            if ans in {"y", "n"}:
                return ans == "y"
            print("Please answer with 'y' or 'n'.")

    @staticmethod
    def _prompt_int_range(question: str, minimum: int, maximum: int) -> int:
        """Ask for an integer within [minimum, maximum] (inclusive)."""
        while True:
            ans = input(f"{question} ({minimum}-{maximum}): ").strip()
            if ans.isdigit() and minimum <= int(ans) <= maximum:
                return int(ans)
            print("Number out of range, please try again.")

    @staticmethod
    def _prompt_multi_select(options: List[str]) -> List[str]:
        """
        Let the user select multiple items by number (comma-separated).
        Return the chosen items as a list.
        """
        for idx, opt in enumerate(options, start=1):
            print(f"  {idx}. {opt}")
        while True:
            raw = input("Enter the corresponding numbers (comma-separated): ").replace(" ", "")
            indices = [s for s in raw.split(",") if s.isdigit()]
            if all(1 <= int(i) <= len(options) for i in indices):
                return [options[int(i) - 1] for i in indices] if indices else []
            print("Invalid selection, please try again.")


# --------------------------------------------------------------------------- #
# Minimal runnable example
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    questionnaire = WorkoutQuestionnaire()
    answers = questionnaire.run()
    path = questionnaire.save_payload(answers, 
                                      file_path=r"personaltrainers\src\personaltrainers\workout_payload.json")        
    print("\n--- Answers saved! ---")
    print(json.dumps(answers, ensure_ascii=False, indent=2))
    print(f"\nJSON file created: {path}")
