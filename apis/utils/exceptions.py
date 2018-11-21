class ParameterException(Exception):
    def __init__(self, message):
        super(ParameterException, self).__init__(message)


class ApiException(Exception):
    """
    General API-related exceptions
    """
    def __init__(self, message):
        super(ApiException, self).__init__(message)