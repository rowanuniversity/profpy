import abc


class Api(abc.ABC):
    def __init__(self, in_public_key, in_private_key, in_url, in_ip_restriction=None):

        self.url = in_url
        self.public_key = in_public_key
        self.private_key = in_private_key
        self.ip_restriction = in_ip_restriction
        self.endpoints = []
        self.endpoint_to_args = {}

        self.uuid = None
        self.time = None
        self.hash = None
        self.token = None

    @abc.abstractmethod
    def _set_args_mapping(self):
        pass

    @abc.abstractmethod
    def _set_endpoints(self):
        pass

    @abc.abstractmethod
    def _hit_endpoint(
        self, valid_args, endpoint_name, get_one=False, request_type="GET", **kwargs
    ):
        pass
