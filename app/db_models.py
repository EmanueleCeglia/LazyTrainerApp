from sqlalchemy import String, Enum, ForeignKey, Integer
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    declarative_base,
)
from sqlalchemy.ext.associationproxy import association_proxy

Base = declarative_base()

class ExerciseMuscle(Base):
    __tablename__ = "exercise_muscles"

    exercise_id: Mapped[int] = mapped_column(
        Integer,
        # exercises è esattamente il nome della __tablename__ = "exercises"
        ForeignKey("exercises.id", ondelete="CASCADE"),
        primary_key=True,
    )
    muscle_id:  Mapped[int] = mapped_column(
        Integer,
        ForeignKey("muscles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role:       Mapped[str | None] = mapped_column(
        Enum("primary", "secondary", name="role_enum"),
        nullable=True,
    )

    # relationship verso i due lati
    exercise: Mapped["Exercise"] = relationship(
        "Exercise",
        back_populates="muscle_associations",
    )
    muscle:   Mapped["Muscle"]   = relationship(
        "Muscle",
        back_populates="exercise_associations",
    )


class ExerciseEquipment(Base):
    __tablename__ = "exercise_equipment"

    exercise_id: Mapped[int] = mapped_column(
        Integer,
        # exercises è esattamente il nome della __tablename__ = "exercises"
        ForeignKey("exercises.id", ondelete="CASCADE"),
        primary_key=True,
    )
    equipment_id:  Mapped[int] = mapped_column(
        Integer,
        ForeignKey("equipment.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role:       Mapped[str | None] = mapped_column(
        Enum("primary", "secondary", name="role_enum"),
        nullable=True,
    )

    # relationship verso i due lati
    exercise: Mapped["Exercise"] = relationship(
        "Exercise",
        back_populates="equipment_associations",
    )
    equipment:   Mapped["Equipment"]   = relationship(
        "Equipment",
        back_populates="exercise_associations",
    )


class Exercise(Base):
    __tablename__ = "exercises"

    id:               Mapped[int]    = mapped_column(Integer, primary_key=True)
    name:             Mapped[str]    = mapped_column(String(100), unique=True, nullable=False)
    exercise_type:    Mapped[str]    = mapped_column(String(100), nullable=False) # compund, single
    body_region:      Mapped[str]    = mapped_column(String(100), nullable=False) # upper body, lower body
    movement_pattern: Mapped[str]    = mapped_column(String(100), nullable=False) # v/h push/pull, legs

    # 1) relazioni verso l’associazione
    muscle_associations: Mapped[list[ExerciseMuscle]] = relationship(
        "ExerciseMuscle",
        back_populates="exercise",
        cascade="all, delete-orphan"
    )
    # 2) proxy per arrivare direttamente ai Muscle
    muscles: Mapped[list["Muscle"]] = association_proxy(
        "muscle_associations",
        "muscle",
    )


class Muscle(Base):
    __tablename__ = "muscles"

    id:   Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    exercise_associations: Mapped[list[ExerciseMuscle]] = relationship(
        "ExerciseMuscle",
        back_populates="muscle",
        cascade="all, delete-orphan"
    )
    exercises: Mapped[list[Exercise]] = association_proxy(
        "exercise_associations",
        "exercise",
    )


class Equipment(Base):
    __tablename__ = "equipment"

    id:   Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    exercise_associations: Mapped[list[ExerciseEquipment]] = relationship(
        "ExerciseEquipment",
        back_populates="equipment",
        cascade="all, delete-orphan"
    )
    exercises: Mapped[list[Exercise]] = association_proxy(
        "exercise_associations",
        "exercise",
    )
