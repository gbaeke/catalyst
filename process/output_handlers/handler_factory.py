from .csv_handler import CSVOutputHandler
from .json_handler import JSONOutputHandler
from .event_grid_handler import EventGridOutputHandler

class OutputHandlerFactory:
    @staticmethod
    def get_handler(handler_type):
        if handler_type == 'csv':
            return CSVOutputHandler()
        elif handler_type == 'json':
            return JSONOutputHandler()
        elif handler_type == 'event_grid':
            return EventGridOutputHandler()
        else:
            raise ValueError(f"Unsupported output handler type: {handler_type}")