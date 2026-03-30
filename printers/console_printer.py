from printers.base import BasePrinter


class ConsolePrinter(BasePrinter):
    def print_receipt(self, text: str) -> None:
        print(text)

    def is_available(self) -> bool:
        return True
