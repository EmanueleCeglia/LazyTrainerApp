from sqlalchemy import String, Enum, ForeignKey, Integer
from sqlalchemy.orm import (
    Mapped, mapped_column, relationship, declarative_base
)
from sqlalchemy.ext.associationproxy import association_proxy
from typing import Callable

Base = declarative_base()

role_enum = Enum("primary", "secondary", name="role_enum")  # <-- definito 1 sola volta

class ExerciseMuscle(Base):
    __tablename__ = "exercise_muscles"
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True
    )
    muscle_id: Mapped[int] = mapped_column(
        ForeignKey("muscles.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str | None] = mapped_column(role_enum, nullable=True)

    exercise: Mapped["Exercise"] = relationship(back_populates="muscle_associations")
    muscle:   Mapped["Muscle"]   = relationship(back_populates="exercise_associations")


class ExerciseEquipment(Base):
    __tablename__ = "exercise_equipment"
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True
    )
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str | None] = mapped_column(role_enum, nullable=True)

    exercise:  Mapped["Exercise"]  = relationship(back_populates="equipment_associations")
    equipment: Mapped["Equipment"] = relationship(back_populates="exercise_associations")


class Exercise(Base):
    __tablename__ = "exercises"
    id:               Mapped[int]  = mapped_column(Integer, primary_key=True)
    name:             Mapped[str]  = mapped_column(String(100), unique=True, nullable=False)
    exercise_type:    Mapped[str]  = mapped_column(String(100), nullable=False)
    body_region:      Mapped[str]  = mapped_column(String(100), nullable=False)
    movement_pattern: Mapped[str]  = mapped_column(String(100), nullable=False)

    muscle_associations:    Mapped[list[ExerciseMuscle]]    = relationship(
        "ExerciseMuscle",
        back_populates="exercise", 
        cascade="all, delete-orphan"
    )
    equipment_associations: Mapped[list[ExerciseEquipment]] = relationship(
        "ExerciseEquipment",
        back_populates="exercise", 
        cascade="all, delete-orphan"
    )

    muscles:    Mapped[list["Muscle"]]    = association_proxy("muscle_associations", "muscle", creator=lambda m: ExerciseMuscle(muscle=m))
    equipments: Mapped[list["Equipment"]] = association_proxy("equipment_associations", "equipment", creator=lambda e: ExerciseEquipment(equipment=e))


class Muscle(Base):
    __tablename__ = "muscles"
    id:   Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    exercise_associations: Mapped[list[ExerciseMuscle]] = relationship(
        back_populates="muscle", cascade="all, delete-orphan"
    )
    exercises: Mapped[list[Exercise]] = association_proxy("exercise_associations", "exercise")


class Equipment(Base):
    __tablename__ = "equipment"
    id:   Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    exercise_associations: Mapped[list[ExerciseEquipment]] = relationship(
        back_populates="equipment", cascade="all, delete-orphan"
    )
    exercises: Mapped[list[Exercise]] = association_proxy("exercise_associations", "exercise")

