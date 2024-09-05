from .base_handler import BaseOutputHandler
from .csv_handler import CSVOutputHandler
from .json_handler import JSONOutputHandler
import os

class OutputHandlerFactory:
    @staticmethod
    def get_handler(handler_type: str = None) -> BaseOutputHandler:
        if handler_type is None:
            handler_type = os.getenv('INVOICE_OUTPUT_HANDLER', 'csv')

        if handler_type.lower() == 'csv':
            return CSVOutputHandler()
        elif handler_type.lower() == 'json':
            return JSONOutputHandler()
        # Add more handlers here as needed
        else:
            raise ValueError(f"Unsupported output handler type: {handler_type}")