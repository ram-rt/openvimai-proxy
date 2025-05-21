from pydantic import BaseModel

class CompletionChunk(BaseModel):
    choices: list
    usage: dict | None = None
