import requests
from xml.etree.ElementTree import fromstring
from . import Api, ParameterException, ApiException


class TwentyFiveLive(Api):
    """
    Class that optimizes api calls to the CollegeNet 25Live REST interface.
    """

    __HTTP_ERRORS = {
        400: "Bad Request",
        403: "Invalid Credentials",
        404: "Invalid endpoint"
    }

    __URL = "https://25live.collegenet.com/25live/data/rowan/run/"
    GET_RESERVATIONS = "/reservations.xml"

    def __init__(self):
        super().__init__(in_public_key=None, in_private_key=None, in_url=self.__URL)
        self._set_endpoints()
        self._set_args_mapping()

    @property
    def authentication_headers(self):
        """
        From parent class, not used in this API
        :return:
        """
        return

    @property
    def authentication_parameters(self):
        """
        From parent class, user/password credentials
        :return:
        """
        return

    def _generate_hash_value(self):
        """
        From parent class, not used in this API
        :return:
        """
        return

    def _update_time(self):
        """
        From parent class, not used in this API
        :return:
        """
        return

    def _set_endpoints(self):
        """
        Sets a list of valid endpoints for this API
        :return:
        """
        self.endpoints = [self.GET_RESERVATIONS]

    def _set_args_mapping(self):
        """
        Sets a mapping for each endpoint, specifying valid input parameters.
        :return:
        """
        self.endpoint_to_args = {
            self.GET_RESERVATIONS: ["space_id", "space_name"]
        }

    def _hit_endpoint(self, valid_args, endpoint_name, get_one=False, request_type="GET", **kwargs):
        """
        Abstracted logic for hitting REST endpoints for this API
        :param valid_args:    Valid keyword arguments for this endpoint (list)
        :param endpoint_name: The endpoint                              (str)
        :param get_one:       Whether or not to get one result          (bool)
        :param request_type:  The type of http request                  (str)
        :param kwargs:        Additional request parameters             (**kwargs)
        :return:              A response object
        """
        if all(arg in valid_args for arg in kwargs):
            full_url = self.url + endpoint_name
            r_type = request_type.upper()
            if r_type == "GET":
                headers = {"Content-Type": "application/xml; charset=utf-8", "Accept": "application/xml"}
                data = requests.get(full_url, params=kwargs, headers=headers, auth=self.authentication_parameters)
                status = int(data.status_code)
                if 300 >= status >= 200:
                    return data
                elif status >= 500:
                    raise ApiException("Internal Server Error.")
                elif status >= 400:
                    try:
                        raise ApiException(self.__HTTP_ERRORS[status])
                    except KeyError:
                        raise ApiException("Error processing request: {0}".format(data.text))
                else:
                    raise ApiException("Unknown error.")
            else:
                raise ApiException("Currently Unsupported!")

        else:
            bad_args = ", ".join(list(kwargs.keys()))
            good_args = ", ".join(valid_args)
            msg = "Invalid parameter supplied at ServiceNowTable::_hit_endpoint(). Arguments provided: {0}. " \
                  "Valid arguments: {1}.".format(bad_args, good_args)
            raise ParameterException(msg)

    def get_reservations(self, as_text=False, **kwargs):
        """
        Returns xml for reservation data in 25Live.
        :param as_text: Whether or not to get the XML as text (bool)
        :param kwargs:  Keyword args for url parameters       (**kwargs)
        :return:        REST call result                      (xml.etree.ElementTree.Element or str)
        """
        endpoint = self.GET_RESERVATIONS
        valid_args = self.endpoint_to_args[endpoint]
        xml_text = self._hit_endpoint(valid_args, endpoint, **kwargs).text
        return xml_text if as_text else fromstring(xml_text)
