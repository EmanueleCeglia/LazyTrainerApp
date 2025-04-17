"""
SQLAlchemy models for LazyTrainer.
Type‑hints follow the SQLAlchemy 2.0 'Mapped' style.
"""

from typing import List
from sqlalchemy import String, Enum, ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    declarative_base,
)

Base = declarative_base()


class Muscle(Base):
    __tablename__ = "muscles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    exercises: Mapped[List["Exercise"]] = relationship(
        secondary="exercise_muscles",
        back_populates="muscles",
    )


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    equipment: Mapped[str | None] = mapped_column(String(100), nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(20), nullable=True)
    calories_burned: Mapped[int | None] = mapped_column(nullable=True)


    muscles: Mapped[List[Muscle]] = relationship(
        secondary="exercise_muscles",
        back_populates="exercises",
    )


class ExerciseMuscle(Base):
    __tablename__ = "exercise_muscles"

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"),
        primary_key=True,
    )
    muscle_id: Mapped[int] = mapped_column(
        ForeignKey("muscles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str | None] = mapped_column(
        Enum("primary", "secondary", name="role_enum"),
        nullable=True,
    )
