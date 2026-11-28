"""A paging window, declared once and reused by any endpoint that returns a list."""
from typing import Annotated

from fastapi import Depends, Query


def get_pagination(
    skip: Annotated[int, Query(ge=0, description="How many entries to step over")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="How many entries to return")] = 20,
) -> dict:
    return {"skip": skip, "limit": limit}


# Declaring the dependency as a type keeps the endpoint signatures short and
# makes the same window impossible to spell differently in two places.
PaginationDep = Annotated[dict, Depends(get_pagination)]
