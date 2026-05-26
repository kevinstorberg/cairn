from typing import TypedDict


def add_messages_reducer(existing: list, new: list) -> list:
    return existing + new


class BaseState(TypedDict):
    messages: list
