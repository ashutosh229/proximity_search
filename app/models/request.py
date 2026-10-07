from pydantic import BaseModel


class SearchResponse(BaseModel):
    locations: list[int]
