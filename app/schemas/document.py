from pydantic import BaseModel
from datetime import datetime


class DocumentMetadata(BaseModel):

    source_url: str
    domain: str
    collected_at: datetime
    approved: bool
    embedding_model: str