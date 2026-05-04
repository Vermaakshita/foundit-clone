from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional, Any

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    page: int
    limit: int
    total_pages: int

    @classmethod
    def create(cls, data: List[T], total: int, page: int, limit: int) -> "PaginatedResponse[T]":
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        return cls(data=data, total=total, page=page, limit=limit, total_pages=total_pages)


class MessageResponse(BaseModel):
    message: str
    success: bool = True
    data: Optional[Any] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Optional[Any] = None
