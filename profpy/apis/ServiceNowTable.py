import requests
import json
from http.client import responses
from . import Api, ParameterException, ApiException


class ServiceNowTable(Api):
    """
    Class that optimizes http calls to the ServiceNowTable REST interface

    Documentation regarding individual endpoints can be found at:
    https://docs.servicenow.com/bundle/london-application-development/page/integrate/inbound-rest/concept/c_TableAPI.html

    Currently only supporting GET requests
    """

    GET_RECORDS = "/{get_table_name}"
    GET_SINGLE_RECORD = "/{get_table_name}/{get_record_id}"
    GET_REQUESTS = [GET_SINGLE_RECORD, GET_RECORDS]

    def __init__(self, user, password, in_url):

        parsed_url = in_url[:-1] if in_url[-1:] == "/" else in_url
        super().__init__(in_public_key=user, in_private_key=password, in_url=parsed_url)
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
            self.GET_RECORDS: [
                "tableName",
                "sysparm_query",
                "sysparm_display_value",
                "sysparm_fields",
                "sysparm_view",
                "sysparm_limit",
                "sysparm_offset",
                "sysparm_exclude_reference_link",
                "sysparm_suppress_pagination_header",
            ],
            self.GET_SINGLE_RECORD: [
                "tableName",
                "sys_id",
                "sysparm_display_value",
                "sysparm_fields",
                "sysparm_view",
                "sysparm_exclude_reference_link",
            ],
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
                    "Content-Type": "application/xml",
                    "Accept": "application/json",
                }
                data = requests.get(
                    full_url,
                    params=kwargs,
                    headers=headers,
                    auth=self.authentication_parameters,
                )
                status = int(data.status_code)
                if 300 >= status >= 200:
                    try:
                        json_obj = data.json()
                        return json_obj["result"] if status == 200 else json_obj
                    except json.JSONDecodeError:
                        raise ApiException(
                            "Transaction cancelled: maximum execution time exceeded.",
                            error_code=408,
                        )
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

    def get_records(self, table_name=None, **kwargs):
        """
        Returns a list of records based on table name and other specified keyword args.
        For information on the xml schema, see:
        https://docs.servicenow.com/bundle/london-application-development/page/integrate/inbound-rest/concept/c_TableAPI.html#r_TableAPI-GET

        :param table_name: The name of the table      (str)
        :param kwargs:     Other keyword arguments    (**kwargs)
        :return:           JSON result                (dict)
        """
        endpoint = self.GET_RECORDS
        valid_args = self.endpoint_to_args[endpoint]
        endpoint = (
            endpoint.format(get_table_name=table_name)
            if table_name
            else endpoint.replace("{get_table_name}", "")
        )
        return self._hit_endpoint(valid_args, endpoint, **kwargs)

    def get_record(self, table_name, record_id, custom_id_field=None, **kwargs):
        """
        Returns a record based on table name, system id, and other specified keyword args.
        For information on the xml schema, see:
        https://docs.servicenow.com/bundle/london-application-development/page/integrate/inbound-rest/concept/c_TableAPI.html#r_TableAPI-GETid
        :param table_name:      The name of the table                                        (str)
        :param record_id:       The id number of the record, hits sys_id by default          (str)
        :param custom_id_field: An id field to use other than the sys_id                     (str) (defaults to None)
        :param kwargs:          Additional request parameters                                (**kwargs)
        :return:                JSON result                                                  (dict)
        """

        if custom_id_field:
            query = "{0}={1}".format(custom_id_field, record_id)
            result = self.get_records(table_name, sysparm_query=query, sysparm_limit=1)
            result = None if not result else result[0]
        else:
            endpoint = self.GET_SINGLE_RECORD
            valid_args = self.endpoint_to_args[endpoint]
            endpoint = endpoint.format(
                get_table_name=table_name, get_record_id=record_id
            )
            result = self._hit_endpoint(valid_args, endpoint, **kwargs)
        return result

    def load_table(self, table_name, limit=None, **kwargs):
        """
        Abstracted logic to fully load all fields for records in a table. This can be used to get around the
        timeout error for larger tables
        :param table_name:   The name of the table                          (str)
        :param limit:        An optional cap on the number records returned (int)
        :param kwargs:       Additional keyword arguments for the endpoint  (**kwargs)
        :return:             JSON result                                    (dict)
        """

        if "sysparm_limit" in kwargs or "sysparm_offset" in kwargs:
            raise ParameterException(
                'ServiceNowTable.load_table method does not allow the use of "sysparm_limit" or '
                '"sysparm_offset" query parameters.'
            )

        keep_going = True
        request_size_limit = 1500

        params = {**kwargs, **dict(sysparm_limit=request_size_limit)}
        results = self.get_records(table_name, **params)
        if len(results) >= request_size_limit:
            current_offset = request_size_limit
            while keep_going:
                params = {
                    **kwargs,
                    **dict(
                        sysparm_offset=current_offset, sysparm_limit=request_size_limit
                    ),
                }
                results.extend(self.get_records(table_name, **params))
                current_offset += request_size_limit
                keep_going = (len(results) >= current_offset) and (
                    (limit and len(results) < limit) or not limit
                )
        return results[:limit] if limit else results
