import logging
from .request_handler import MethodType, RequestHandlerContext, RequestHandler

class RequestMapper:

    def __init__(self):
        self.handlers = {}

    def add_request_handler(self, handler : RequestHandler):
        handler_key = (handler.resource, handler.method_type)

        if handler_key in self.handlers.keys():
            logging.warn('Cannot register duplicate handeler \'{}\' for (resource=\'{}\'/method=\'{}\') - handler \'{}\' is already registered'.format(
                handler.name,
                handler.resource,
                handler.method_type.name,
                self.handlers.get(handler_key).name
            ))

        else:
            print('Registering handler \'{}\' for (resource=\'{}\'/method=\'{}\')'.format(
                handler.name,
                handler.resource,
                handler.method_type.name,
            ))
            self.handlers[handler_key] = handler

    def get_handler(self, resource : str, method_type : MethodType ):
        handler_key = (resource, method_type)
        return self.handlers.get(handler_key) if handler_key in self.handlers.keys() else None
