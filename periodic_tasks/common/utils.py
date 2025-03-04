from typing import Iterator, TypeVar

T = TypeVar('T')


def to_chunks(items: list[T], size: int) -> Iterator[list[T]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]
