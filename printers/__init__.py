from printers.base import BasePrinter
from printers.console_printer import ConsolePrinter


def get_printer(printer_type: str) -> BasePrinter:
    if printer_type == "console":
        return ConsolePrinter()
    elif printer_type == "thermal":
        try:
            from printers.thermal_printer import ThermalPrinter

            return ThermalPrinter()
        except ImportError:
            raise SystemExit(
                "python-escpos not installed. Run: uv sync --extra hardware"
            )
    else:
        raise SystemExit(f"Unknown printer type: {printer_type}")
