from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator

from models import Workload


class WorkerAddDTO(BaseModel):
    username: str


class WorkerDTO(WorkerAddDTO):
    id: UUID

    @field_validator("id") # кастит UUID к str
    def validate_uuids(cls, value):
        if value:
            return str(value)
        return value


class ResumeAddDTO(BaseModel):
    title: str
    compensation: Optional[int]
    workload: Workload
    worker_id: UUID

    @field_validator("worker_id")  # кастит UUID к str
    def validate_uuids(cls, value):
        if value:
            return str(value)
        return value


class ResumeDTO(ResumeAddDTO):
    id: UUID
    created_at: datetime
    updated_at: datetime

    @field_validator("id")  # кастит UUID к str
    def validate_uuids(cls, value):
        if value:
            return str(value)
        return value


class ResumesRelDTO(ResumeDTO):
    worker: "WorkerDTO"


class WorkerRelDTO(WorkerDTO):
    resumes: list["ResumeDTO"]


class VacancyAddDTO(BaseModel):
    title: str
    compensation: Optional[int]


class VacancyDTO(VacancyAddDTO):
    id: UUID

    @field_validator("id")  # кастит UUID к str
    def validate_uuids(cls, value):
        if value:
            return str(value)
        return value


class ResumesRelVacanciesRepliedDTO(ResumeDTO):
    worker: "WorkerDTO"
    vacancies_replied: list["VacancyDTO"]