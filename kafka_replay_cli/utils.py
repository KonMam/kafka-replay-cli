from typing import Optional


def validate_positive(value: Optional[int], name: str):
    if value is not None and value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
