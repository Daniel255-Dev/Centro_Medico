from datetime import datetime
from typing import Annotated, Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from pydantic_core import core_schema


class _ObjectIDPydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        def validate(v):
            if isinstance(v, ObjectId):
                return str(v)
            if isinstance(v, str) and ObjectId.is_valid(v):
                return v
            raise ValueError("ID invalido de MongoDB (ObjectId)")

        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.no_info_plain_validator_function(validate),
            serialization=core_schema.to_string_ser_schema(),
        )


pyObjectId = Annotated[str, _ObjectIDPydanticAnnotation()]


class CitaMedicaBase(BaseModel):
    paciente: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Nombre completo del paciente",
    )
    doctor: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Nombre del médico tratante",
    )
    especialidad: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Especialidad médica de la cita",
    )
    fecha: datetime = Field(..., description="Fecha y hora programada para la cita")

    @field_validator("fecha", mode="before")
    @classmethod
    def parse_fecha(cls, value):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%d-%m-%Y %H:%M")
            except ValueError:
                return value
        return value

    @field_serializer("fecha", when_used="json")
    def serialize_fecha(self, value: datetime) -> str:
        return value.strftime("%d-%m-%Y %H:%M")

    motivo: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Motivo o observación de la cita",
    )
    estado: str = Field(
        default="programada",
        max_length=50,
        description="Estado de la cita",
    )


class CitaMedicaCreate(CitaMedicaBase):
    pass


class CitaMedicaUpdate(BaseModel):
    paciente: Optional[str] = Field(None, min_length=3, max_length=150)
    doctor: Optional[str] = Field(None, min_length=3, max_length=150)
    especialidad: Optional[str] = Field(None, min_length=3, max_length=100)
    fecha: Optional[datetime] = None

    @field_validator("fecha", mode="before")
    @classmethod
    def parse_fecha(cls, value):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%d-%m-%Y %H:%M")
            except ValueError:
                return value
        return value

    motivo: Optional[str] = Field(None, max_length=500)
    estado: Optional[str] = Field(None, max_length=50)


class CitaMedicaResponse(CitaMedicaBase):
    id: pyObjectId = Field(alias="_id", description="Identificador único de MongoDB")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "_id": "654321abcdef012345678",
                "paciente": "Ana García",
                "doctor": "Dr. Daniel Ovalle",
                "especialidad": "Cardiología",
                "fecha": "11-08-2023 10:00",
                "motivo": "Control de presión arterial",
                "estado": "programada",
            }
        },
    )
