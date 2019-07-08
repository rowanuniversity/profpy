import requests
import datetime
from xml.etree.ElementTree import fromstring
from http.client import responses
from . import Api, ParameterException, ApiException

NAMESPACE = "{http://www.collegenet.com/r25}"


class TwentyFiveLive(Api):
    """
    Class that optimizes api calls to the CollegeNet 25Live REST interface.
    """

    __NAMESPACE = "{http://www.collegenet.com/r25}"
    GET_RESERVATIONS = "/reservations.xml"
    GET_SPACES = "/spaces.xml"
    GET_ORGS = "/organizations.xml"
    GET_ORG_TYPES = "/orgtypes.xml"
    GET_RATE_GROUPS = "/rategrp.xml"

    def __init__(self, in_url):
        super().__init__(in_public_key=None, in_private_key=None, in_url=in_url)
        self._set_endpoints()
        self._set_args_mapping()

    def _set_endpoints(self):
        """
        Sets a list of valid endpoints for this API
        :return:
        """
        self.endpoints = [
            self.GET_RESERVATIONS,
            self.GET_ORGS,
            self.GET_SPACES,
            self.GET_RATE_GROUPS,
        ]

    def _set_args_mapping(self):
        """
        Sets a mapping for each endpoint, specifying valid input parameters.
        :return:
        """
        self.endpoint_to_args = {
            self.GET_RESERVATIONS: ["space_id"],
            self.GET_SPACES: ["space_id"],
            self.GET_ORGS: ["organization_id"],
            self.GET_ORG_TYPES: ["type_id"],
            self.GET_RATE_GROUPS: ["rate_group_id"],
        }

    def _hit_endpoint(
        self, valid_args, endpoint_name, get_one=False, request_type="GET", **kwargs
    ):
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
                headers = {
                    "Content-Type": "application/xml; charset=utf-8",
                    "Accept": "application/xml",
                }
                data = requests.get(full_url, params=kwargs, headers=headers)
                status = int(data.status_code)
                if 300 >= status >= 200:
                    return data
                elif status >= 500:
                    raise ApiException("Internal Server Error.")
                elif status >= 400:
                    try:
                        raise ApiException(responses[status])
                    except KeyError:
                        raise ApiException(
                            "Error processing request: {0}".format(data.text)
                        )
                else:
                    raise ApiException("Unknown error.")
            else:
                raise ApiException("Currently Unsupported!")

        else:
            bad_args = ", ".join(list(kwargs.keys()))
            good_args = ", ".join(valid_args)
            msg = (
                "Invalid parameter supplied at ServiceNowTable::_hit_endpoint(). Arguments provided: {0}. "
                "Valid arguments: {1}.".format(bad_args, good_args)
            )
            raise ParameterException(msg)

    def get_organizations(self, as_xml_text=False, **kwargs):
        """
        Returns JSON (or xml text) for organization data in 25Live
        :param as_xml_text: Whether or not to get the result as an xml str (bool)
        :param kwargs:      Keyword args for url parameters                (**kwargs)
        :return:            REST call result                               (list or str)
        """
        endpoint = self.GET_ORGS
        valid_args = self.endpoint_to_args[endpoint]
        data = self._hit_endpoint(valid_args, endpoint, **kwargs).text
        if as_xml_text:
            result = data
        else:
            result = []
            for organization in fromstring(data).findall(
                self.__NAMESPACE + "organization"
            ):
                result.append(parse_organization_from_xml(organization))
        return result

    def get_organization_types(self, as_xml_text=False, **kwargs):
        """
        Returns JSON (or xml text) for organization type data in 25Live
        :param as_xml_text: Whether or not to get the result as an xml str (bool)
        :param kwargs:      Keyword args for url parameters                (**kwargs)
        :return:            REST call result                               (list or str)
        """
        endpoint = self.GET_ORG_TYPES
        valid_args = self.endpoint_to_args[endpoint]
        data = self._hit_endpoint(valid_args, endpoint, **kwargs).text
        if as_xml_text:
            result = data
        else:
            result = []
            for org_type in fromstring(data).findall(self.__NAMESPACE + "type"):
                result.append(parse_organization_type_from_xml(org_type))
        return result

    def get_reservations(self, as_xml_text=False, **kwargs):
        """
        Returns JSON (or xml text) for reservation data in 25Live.
        :param as_xml_text: Whether or not to get the result as an xml str (bool)
        :param kwargs:      Keyword args for url parameters                (**kwargs)
        :return:            REST call result                               (list or str)
        """
        endpoint = self.GET_RESERVATIONS
        valid_args = self.endpoint_to_args[endpoint]
        data = self._hit_endpoint(valid_args, endpoint, **kwargs).text
        if as_xml_text:
            result = data
        else:
            result = []
            for space in fromstring(data).findall(self.__NAMESPACE + "reservation"):
                result.append(parse_reservation_from_xml(space))
        return result

    def get_spaces(self, as_xml_text=False, **kwargs):
        """
        Returns JSON (or xml text) for space data in 25Live.
        :param as_xml_text: Whether or not to get the result as an xml str (bool)
        :param kwargs:      Keyword args for the url parameters            (**kwargs)
        :return:            REST call result                               (list or str)
        """
        endpoint = self.GET_SPACES
        valid_args = self.endpoint_to_args[endpoint]
        data = self._hit_endpoint(valid_args, endpoint, **kwargs).text
        if as_xml_text:
            result = data
        else:
            result = []
            for space in fromstring(data).findall(self.__NAMESPACE + "space"):
                result.append(parse_space_from_xml(space))
        return result


def reformat_timezone_offset(in_date_string):
    """
    Reformats the datetime string to get rid of the colon in the timezone offset
    :param in_date_string: The datetime string    (str)
    :return:               The reformatted string (str)
    """
    out_data = in_date_string
    if ":" == in_date_string[-3:-2]:
        out_data = out_data[:-3] + out_data[-2:]
    return out_data


def get_text_from_element(parent_element_object, element_name, namespace, is_dt=False):
    """
    Returns the text from an xml element
    :param parent_element_object: The parent xml object                   (xml.etree.ElementTree.Element)
    :param element_name:          The name of the child                   (str)
    :param namespace:             The xml namespace                       (str)
    :param is_dt:                 Whether or not this is a datetime value (bool)
    :return:
    """
    child = parent_element_object.find(namespace + element_name)
    fmt = "%Y-%m-%dT%H:%M:%S%z"
    data = None
    if child is not None:
        data = child.text
        if is_dt:
            data = datetime.datetime.strptime(reformat_timezone_offset(data), fmt)

    return data


def parse_organization_from_xml(in_xml):
    """
    Parses JSON from an input xml object for a 25Live organization type
    :param in_xml: The 25Live organization xml object (xml.etree.ElementTree.Element)
    :return:       The parsed JSON                    (dict)
    """
    result = {}
    for child in in_xml:
        tag = child.tag.replace(NAMESPACE, "")
        if tag == "organization_type":
            type_element = in_xml.find(NAMESPACE + "organization_type")
            type_json = {}
            for type_child in type_element:
                type_tag = type_child.tag.replace(NAMESPACE, "")
                type_json[type_tag] = get_text_from_element(
                    type_element, type_tag, NAMESPACE
                )
            result[tag] = type_json
        else:
            result[tag] = get_text_from_element(
                in_xml, tag, NAMESPACE, is_dt=tag == "last_mod_dt"
            )
    return result


def parse_organization_type_from_xml(in_xml):
    """
    Parses JSON from an input xml object for a 25Live organization type
    :param in_xml: The 25Live organization type xml object (xml.etree.ElementTree.Element)
    :return:       The parsed JSON                         (dict)
    """
    result = {}
    for child in in_xml:
        tag = child.tag.replace(NAMESPACE, "")
        if tag == "rate_group":
            rg_element = in_xml.find(NAMESPACE + "rate_group")
            rg_json = {}
            for rg_child in rg_element:
                rg_tag = rg_child.tag.replace(NAMESPACE, "")
                rg_json[rg_tag] = get_text_from_element(rg_element, rg_tag, NAMESPACE)
            result[tag] = rg_json
        else:
            result[tag] = get_text_from_element(
                in_xml, tag, NAMESPACE, is_dt=tag == "last_mod_dt"
            )
    return result


def parse_space_from_xml(in_xml):
    """
    Parses JSON from an input xml object for a 25Live space
    :param in_xml: The 25Live space xml object (xml.etree.ElementTree.Element)
    :return:       The parsed JSON             (dict)
    """
    result = {}
    for child in in_xml:
        tag = child.tag.replace(NAMESPACE, "")
        result[tag] = get_text_from_element(
            in_xml, tag, NAMESPACE, is_dt=tag == "last_mod_dt"
        )
    return result


def parse_reservation_from_xml(in_xml):
    """
    Parses JSON from an input xml object for a 25Live reservation
    :param in_xml: The 25Live reservation xml object (xml.etree.ElementTree.Element)
    :return:       The parsed JSON                   (dict)
    """
    dates = [
        "reservation_start_dt",
        "pre_event_dt",
        "event_start_dt",
        "event_end_dt",
        "post_event_dt",
        "reservation_end_dt",
        "last_mod_dt",
    ]
    result = {}
    for child in in_xml:
        tag = child.tag.replace(NAMESPACE, "")
        if tag == "space_reservation":
            space_data = in_xml.find(NAMESPACE + "space_reservation")
            space_json = {}
            for space_child in space_data:
                space_tag = space_child.tag.replace(NAMESPACE, "")
                space_json[space_tag] = get_text_from_element(
                    space_data, space_tag, NAMESPACE
                )
            result[tag] = space_json
        else:
            result[tag] = get_text_from_element(
                in_xml, tag, NAMESPACE, is_dt=tag in dates
            )
    return result
