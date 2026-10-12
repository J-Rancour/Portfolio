"""Request/response schemas. Pydantic validates input and documents the API (see /docs)."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

Station = str  # 4-letter ICAO identifier, e.g. KJFK


class ObservationBase(BaseModel):
    station: Station = Field(pattern=r"^[A-Z]{4}$", examples=["KJFK"])
    observed_at: datetime = Field(examples=["2026-10-11T18:51:00Z"])
    temperature_c: float = Field(ge=-90, le=60)
    dewpoint_c: float = Field(ge=-90, le=60)
    wind_dir_deg: int = Field(ge=0, le=360)
    wind_speed_kt: int = Field(ge=0, le=250)
    visibility_sm: float = Field(ge=0, le=100, description="Statute miles")
    ceiling_ft: int | None = Field(
        default=None, ge=0, description="Lowest BKN/OVC layer in feet AGL; null = no ceiling"
    )
    raw_metar: str | None = None

    @field_validator("station", mode="before")
    @classmethod
    def upper_station(cls, v):
        return v.upper() if isinstance(v, str) else v

    @model_validator(mode="after")
    def dewpoint_not_above_temperature(self):
        # Cross-field rule: field-level checks can't see two fields at once.
        if self.dewpoint_c > self.temperature_c:
            raise ValueError("dewpoint_c cannot be higher than temperature_c")
        return self


class ObservationCreate(ObservationBase):
    pass


class ObservationPatch(BaseModel):
    """Every field optional: PATCH changes only what the client sends."""

    temperature_c: float | None = Field(default=None, ge=-90, le=60)
    dewpoint_c: float | None = Field(default=None, ge=-90, le=60)
    wind_dir_deg: int | None = Field(default=None, ge=0, le=360)
    wind_speed_kt: int | None = Field(default=None, ge=0, le=250)
    visibility_sm: float | None = Field(default=None, ge=0, le=100)
    ceiling_ft: int | None = Field(default=None, ge=0)
    raw_metar: str | None = None


class Observation(ObservationBase):
    id: str
    flight_category: str  # computed by the C++ core (see app/wxcore.py)


class ObservationPage(BaseModel):
    items: list[Observation]
    total: int
    limit: int
    offset: int
