import requests
import uuid
import hashlib
import time
import datetime
from .utils import ParameterException, Api


class CampusLabs(Api):
    """
     Class that optimizes http calls to the Campus Labs REST interface
     """

    # class-wide constants
    __MAX_PAGE_SIZE = 500
    __RATE_LIMIT_CODE = 429
    __RATE_LIMIT_PM = 400
    __RATE_LIMIT_PS = 30
    __RATE_LIMIT_SLEEP = 5

    def __init__(self, in_public_key, in_private_key, in_ip_address):
        """
         Constructor
         :param in_public_key:  The provided developer api key
         :param in_private_key: The provided private key
         :param in_ip_address:  The ip address that these requests will be made from
         """

        super(CampusLabs, self).__init__(in_public_key, in_private_key, "https://rowan.campuslabs.com/engage/api/",
                                         in_ip_address)
        self.uuid = str(uuid.uuid4())

    @property
    def authentication_headers(self):
        return {}

    @property
    def authentication_parameters(self):
        """
         The parameters used to authenticate to the REST service
         :return: A dictionary of authentication parameters
         """
        return {"time": self.time, "ipaddress": self.ip_restriction, "apikey": self.public_key,
                "random": self.uuid, "hash": self.hash}

    def __set_endpoints(self):
        self.endpoints = ["organizations", "memberships", "positions", "users"]

    def __set_args_mapping(self):
        self.endpoint_to_args = {
            "organizations": ["organizationId", "page", "pageSize", "status", "excludeHiddenOrganizations", "category",
                              "type", "name", "ModifiedOnStart", "ModifiedOnEnd"],
            "memberships": ["page", "pageSize", "membershipId", "userId", "username", "organizationId",
                            "currentMembershipsOnly", "publicPrivacyFilter", "campusPrivacyFilter",
                            "includeReflections", "positionTemplateId", "positionTemplateName", "startDate", "endDate",
                            "ModifiedOnStart", "ModifiedOnEnd", "includeDeletes"],
            "positions": ["page", "pageSize", "organizationId", "template", "type", "activeStatusOnly"],
            "users": ["page", "pageSize", "userId", "username", "cardId", "sisId", "affiliation", "enrollmentStatus",
                      "SchoolOfEnrollment", "status", "CreatedOnStart", "CreatedOnEnd"]
        }

    def __update_time(self):
        """
         Updates the time and hash properties of the object. This gets called every time the api is called.
         :return:
         """
        self.__time = str(int(round(time.time() * 1000.0)))
        self.__hash = self.__generate_hash_value()

    def __generate_hash_value(self):
        """
         Generates the sha-512 hash for this session
         :return:  the hash value in hex
         """
        hasher = hashlib.sha512()
        for value in (self.public_key, self.ip_restriction, self.time, self.uuid, self.private_key):
            hasher.update(value.encode())
        return hasher.hexdigest()

    def __hit_endpoint(self, valid_args, endpoint_name, get_one=False, request_type="GET", **kwargs):
        """
         Wrapper method for calling a REST endpoint
         :param valid_args:    A collection containing the valid url parameters for the desired endpoint
         :param endpoint_name: The name of the endpoint being called
         :param kwargs:        A dictionary of optional parameters to further filter the results
         :return:              The GET request object
         """

        # only do work if all of the given parameters are valid
        if all(arg in valid_args for arg in kwargs.keys()):
            self.__update_time()
            params = dict(self.authentication_parameters, **kwargs)

            if "pageSize" not in params.keys():
                params["pageSize"] = self.__MAX_PAGE_SIZE

            # hit the endpoint and return the resulting data
            full_url = self.url + endpoint_name
            data = requests.get(full_url, params).json()

            # if they specified the page, give them whatever is returned
            if "page" in params.keys():
                return_data = data["items"]

            # if not, give them all possible data on all pages
            else:

                num_pages = data["totalPages"]

                # if there is 1 or no pages, just return the "items" array. If not, we have to hit endpoint for each
                # page to get all results
                if num_pages < 2:
                    return_data = data["items"]
                else:
                    parsed_data = data["items"]
                    start = datetime.datetime.now()
                    request_count = 0
                    for page in range(2, num_pages + 1):

                        # we have to update our time and hash params to ensure that we can make valid calls to the api
                        self.__update_time()
                        params = dict(self.authentication_parameters, **kwargs)

                        # dynamically switch pages and grab the new data
                        params["page"] = page
                        params["pageSize"] = self.__MAX_PAGE_SIZE
                        request = requests.get(full_url, params)
                        request_count += 1

                        # if we get a 429, that means we hit the rate limit, wait a minute and then resume at the same
                        # page number
                        if request.status_code == self.__RATE_LIMIT_CODE:

                            elapsed_seconds = (datetime.datetime.now() - start).total_seconds()
                            per_second = request_count / elapsed_seconds
                            per_minute = request_count / (elapsed_seconds / 60)

                            print("Hit rate limit, waiting.")
                            if per_minute >= self.__RATE_LIMIT_PM or per_second >= self.__RATE_LIMIT_PS:
                                time.sleep(self.__RATE_LIMIT_SLEEP)
                            else:
                                raise Exception("Rate limit exceeded.")
                            page -= 1
                        else:
                            parsed_data.extend(request.json()["items"])

                    return_data = parsed_data

            return return_data[0] if get_one and len(return_data) > 0 else return_data

        # if not, raise an exception
        else:
            raise ParameterException("Invalid parameter supplied.")

    # The following methods call individual REST endpoints within the api. They can all kwargs specific to each
    # endpoint, i.e. get_organizations(organizationId=22314)
    #
    # If no kwargs are specified, they return all records found in the system
    def get_users(self, get_one=False, **kwargs):
        endpoint = "users"
        return self.__hit_endpoint(self.endpoint_to_args[endpoint], endpoint, get_one, **kwargs)

    def get_positions(self, get_one=False, **kwargs):
        endpoint = "positions"
        return self.__hit_endpoint(self.endpoint_to_args[endpoint], endpoint, get_one, **kwargs)

    def get_memberships(self, get_one=False, **kwargs):
        endpoint = "memberships"
        return self.__hit_endpoint(self.endpoint_to_args[endpoint], endpoint, get_one, **kwargs)

    def get_organizations(self, get_one=False, **kwargs):
        endpoint = "organizations"
        return self.__hit_endpoint(self.endpoint_to_args[endpoint], endpoint, get_one, **kwargs)
