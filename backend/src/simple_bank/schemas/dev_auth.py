from pydantic import BaseModel, ConfigDict, Field, StrictStr


class DemoProfileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_id: str
    label: str


class DemoSignInRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_id: StrictStr = Field(min_length=1, max_length=64)


class DevAuthSessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fake_auth_enabled: bool
    authenticated: bool
    profiles: list[DemoProfileResponse]
    current_profile: DemoProfileResponse | None = None
