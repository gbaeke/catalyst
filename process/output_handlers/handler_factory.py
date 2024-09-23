from .csv_handler import CSVOutputHandler
from .json_handler import JSONOutputHandler
from .event_grid_handler import EventGridOutputHandler
from .pusher_handler import PusherOutputHandler

class OutputHandlerFactory:
    @staticmethod
    def get_handlers(handler_types):
        handlers = []
        for handler_type in handler_types:
            if handler_type == 'csv':
                handlers.append(CSVOutputHandler())
            elif handler_type == 'json':
                handlers.append(JSONOutputHandler())
            elif handler_type == 'event_grid':
                handlers.append(EventGridOutputHandler())
            elif handler_type == 'pusher':
                handlers.append(PusherOutputHandler())
            else:
                raise ValueError(f"Unsupported output handler type: {handler_type}")
        return handlers