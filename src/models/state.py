from typing import Annotated, TypedDict

from langgraph.graph import add_messages


class BaseState(TypedDict):
    messages: Annotated[list, add_messages]


class TodoBreakdownState(TypedDict):
    """State for todo breakdown graph."""

    messages: Annotated[list, add_messages]
    todo_id: str
    todo_title: str
    todo_description: str
    subtasks_created: list[dict]


class TodoCategorizeState(TypedDict):
    """State for todo categorization graph."""

    messages: Annotated[list, add_messages]
    todo_id: str
    todo_text: str
    category: str | None
