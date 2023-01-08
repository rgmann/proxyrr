class ProxyError(Exception):

    def __init__(self, code, type : str, message : str) -> None:
        self.code = code
        self.type = type
        self.message = message
        super().__init__(self.message)
