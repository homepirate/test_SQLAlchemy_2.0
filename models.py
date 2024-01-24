import datetime
from uuid import uuid4

from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID, ForeignKey, func, String, Index, CheckConstraint
import enum

from typing import Annotated


idpk = Annotated[str, mapped_column(type_=UUID, primary_key=True, default=uuid4)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=func.now())] #server_default для получения даты с сервера БД или
                                                                                        # можно просто default= для получения данных со стороны приложения
updated_at = Annotated[datetime.datetime, mapped_column(server_default=func.now(), onupdate=datetime.datetime.now)]


class Worker(Base):
    __tablename__ = "workers"
    id: Mapped[idpk]
    username: Mapped[str]

    resumes: Mapped[list["Resume"]] = relationship(back_populates="worker")

    resumes_parttime: Mapped[list["Resume"]] = relationship(
        back_populates="worker",
        primaryjoin="and_(Worker.id == Resume.worker_id, Resume.workload == 'parttime')"
    ) # подгрузит при join только те резюме, где workload == parttime


class Workload(enum.Enum):
    parttime = "parttime"
    fulltime = "fulltime"


class Resume(Base):
    __tablename__ = "resumes"
    id: Mapped[idpk]
    title: Mapped[str] = mapped_column(String(50)) # ограничение длинны
    compensation: Mapped[int] = mapped_column(nullable=True)
#   или compensation: Mapped[int | None]
    workload: Mapped[Workload]
    worker_id: Mapped[str] = mapped_column(ForeignKey("workers.id", ondelete="CASCADE")) #для каскадного удаления при удалении работника
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    worker: Mapped["Worker"] = relationship(back_populates="resumes")
    vacancies_replied: Mapped[list["Vacancy"]] = relationship(back_populates="resumes_replied", secondary="vacancies_replies")

    __table_args__ = (
        Index("title_index", "title"),
        CheckConstraint("compensation > 0", "check_compensation_positive")
    )


class Vacancy(Base):
    __tablename__ = "vacancies"

    id: Mapped[idpk]
    title: Mapped[str]
    compensation: Mapped[int] = mapped_column(nullable=True)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    resumes_replied: Mapped[list["Resume"]] = relationship(back_populates="vacancies_replied", secondary="vacancies_replies")


class VacancyReply(Base):
    """
        ДЛЯ СВЯЗИ M2M
        Может быть больше двух полей
    """

    __tablename__ = "vacancies_replies"

    resume_id: Mapped[idpk] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"),
                                            primary_key=True)
    vacancy_id: Mapped[idpk] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), primary_key=True)
    cover_letter: Mapped[str] = mapped_column(nullable=True)

