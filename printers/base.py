from abc import ABC, abstractmethod


class BasePrinter(ABC):
    @abstractmethod
    def print_receipt(self, text: str) -> None:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass
