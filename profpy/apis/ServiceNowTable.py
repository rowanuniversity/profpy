import requests
from xml.dom import minidom
from xml.etree.ElementTree import fromstring, tostring
from http.client import responses
from . import Api, ParameterException, ApiException


class ServiceNowTable(Api):
    """
    Class that optimizes http calls to the ServiceNowTable REST interface

    Documentation regarding individual endpoints can be found at:
    https://docs.servicenow.com/bundle/london-application-development/page/integrate/inbound-rest/concept/c_TableAPI.html

    Currently only supporting GET requests
    """

    GET_RECORDS    = "/table/{get_table_name}"
    GET_SINGLE_RECORD   = "/table/{get_table_name}/{get_record_id}"

    GET_REQUESTS  = [GET_SINGLE_RECORD, GET_RECORDS]

    def __init__(self, user, password, in_url):
        super().__init__(in_public_key=user, in_private_key=password, in_url=in_url)
        self._set_endpoints()
        self._set_args_mapping()

    @property
    def authentication_parameters(self):
        """
        From parent class, user/password credentials
        :return:
        """
        return self.public_key, self.private_key

    def _set_endpoints(self):
        """
        Sets a list of valid endpoints for this API
        :return:
        """
        self.endpoints = [self.GET_SINGLE_RECORD, self.GET_RECORDS]

    def _set_args_mapping(self):
        """
        Sets a mapping for each endpoint, specifying valid input parameters.
        :return:
        """
        self.endpoint_to_args = {
            self.GET_RECORDS: ["tableName", "sysparm_query", "sysparm_display_value", "sysparm_fields", "sysparm_view",
                               "sysparm_limit", "sysparm_offset", "sysparm_exclude_reference_link",
                               "sysparm_suppress_pagination_header"],
            self.GET_SINGLE_RECORD: ["tableName", "sys_id", "sysparm_display_value", "sysparm_fields", "sysparm_view",
                                     "sysparm_exclude_reference_link"]
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
                        raise ApiException(responses[status])
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

    def get_records(self, table_name=None, as_text=False, **kwargs):
        """
        Returns a list of records based on table name and other specified keyword args.
        For information on the xml schema, see:
        https://docs.servicenow.com/bundle/london-application-development/page/integrate/inbound-rest/concept/c_TableAPI.html#r_TableAPI-GET

        :param table_name: The name of the table      (str)
        :param as_text:    Whether or not to receive the XML as text (bool)
        :param kwargs:     Other keyword arguments    (**kwargs)
        :return:           XML result of the API call (xml.etree.ElementTree.Element, or str see: as_text)
        """
        endpoint = self.GET_RECORDS
        valid_args = self.endpoint_to_args[endpoint]
        endpoint = endpoint.format(get_table_name=table_name) if table_name else endpoint.replace("{get_table_name}", "")
        xml_data = fromstring(self._hit_endpoint(valid_args, endpoint, **kwargs).content)
        return self.to_xml_text(xml_data) if as_text else xml_data

    def get_record(self, table_name, sys_id, as_text=False, **kwargs):
        """
        Returns a record based on table name, system id, and other specified keyword args.
        For information on the xml schema, see:
        https://docs.servicenow.com/bundle/london-application-development/page/integrate/inbound-rest/concept/c_TableAPI.html#r_TableAPI-GETid
        :param table_name: The name of the table                     (str)
        :param sys_id:     The id of the record                      (str)
        :param as_text:    Whether or not to receive the XML as text (bool)
        :param kwargs:     Additional request parameters             (**kwargs)
        :return:           XML result of the API call                (xml.etree.ElementTree.Element, or str see: as_text)
        """
        endpoint = self.GET_SINGLE_RECORD
        valid_args = self.endpoint_to_args[endpoint]
        endpoint = endpoint.format(get_table_name=table_name, get_record_id=sys_id)
        xml_data = fromstring(self._hit_endpoint(valid_args, endpoint, **kwargs).content)
        return self.to_xml_text(xml_data) if as_text else xml_data

    @staticmethod
    def to_xml_text(in_xml):
        return minidom.parseString(tostring(in_xml)).toprettyxml(indent="    ")
