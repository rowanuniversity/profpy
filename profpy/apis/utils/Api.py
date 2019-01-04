import abc


class Api(abc.ABC):

    def __init__(self, in_public_key, in_private_key, in_url, in_ip_restriction=None):

        self.public_key       = in_public_key
        self.private_key      = in_private_key
        self.url              = in_url
        self.ip_restriction   = in_ip_restriction
        self.endpoints        = []
        self.endpoint_to_args = {}

        self.uuid  = None
        self.time  = None
        self.hash  = None
        self.token = None

    def parse_endpoint(self, endpoint_name, **kwargs):
        if endpoint_name in self.endpoints and \
                all(arg in self.endpoint_to_args[endpoint_name] for arg in kwargs.keys()):

            self._update_time()
            params = dict(self.authentication_parameters, **kwargs)
            return self.url + "{0}?{1}".format(endpoint_name, "&".join("{0}={1}".format(k, v)
                                                                       for k, v in params.items()))
        else:
            return None

    @property
    @abc.abstractmethod
    def authentication_parameters(self):
        return {}

    @property
    @abc.abstractmethod
    def authentication_headers(self):
        return {}

    @abc.abstractmethod
    def _set_args_mapping(self):
        pass

    @abc.abstractmethod
    def _set_endpoints(self):
        pass

    @abc.abstractmethod
    def _hit_endpoint(self, valid_args, endpoint_name, get_one=False, request_type="GET", **kwargs):
        pass

    @abc.abstractmethod
    def _generate_hash_value(self):
        pass

    @abc.abstractmethod
    def _update_time(self):
        pass