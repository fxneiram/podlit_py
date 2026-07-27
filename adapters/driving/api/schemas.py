from pydantic import BaseModel


class TaskCreateRequest(BaseModel):
    """A task's raw content, in the same Python-literal-syntax text that
    Task.validate_input already expects (e.g. '{1: {"text": "...", "language": "en"}}') -
    matching what a user pastes from the ChatGPT prompt template today.
    """

    raw_text: str


class TaskResponse(BaseModel):
    id: str
    data: dict


class QueueReplaceRequest(BaseModel):
    raw_texts: list[str]


class QueueProcessRequest(BaseModel):
    task_delay_ms: int = 0
    mix_queue: bool = False
