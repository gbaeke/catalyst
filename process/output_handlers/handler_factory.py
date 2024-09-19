from .csv_handler import CSVOutputHandler
from .json_handler import JSONOutputHandler
from .event_grid_handler import EventGridOutputHandler
from .pusher_handler import PusherOutputHandler

class OutputHandlerFactory:
    @staticmethod
    def get_handler(handler_type):
        if handler_type == 'csv':
            return CSVOutputHandler()
        elif handler_type == 'json':
            return JSONOutputHandler()
        elif handler_type == 'event_grid':
            return EventGridOutputHandler()
        elif handler_type == 'pusher':
            return PusherOutputHandler()
        else:
            raise ValueError(f"Unsupported output handler type: {handler_type}")