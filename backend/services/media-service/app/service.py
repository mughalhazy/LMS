"""Service layer."""


class Service:
    """Base service contract that must be implemented by a concrete adapter."""

    def __init__(self) -> None:
        raise NotImplementedError("Service is not implemented for this module")
