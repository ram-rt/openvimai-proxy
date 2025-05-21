from pydantic import BaseModel, Field

class CompletionRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    mode: str = Field("completion", pattern="^(completion|edit)$")
    stream: bool = True