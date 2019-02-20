import base64
import requests
from http.client import responses
from . import Api, ApiException, ParameterException, Token


class BlackBoardLearn(Api):
    """
    Class that optimizes http calls to the BlackBoard REST interface

    Documentation regarding individual endpoints can be found at:
    https://developer.blackboard.com/portal/displayApi
    """

    COLUMNS                    = "v1/courses/{0}/gradebook/columns"
    COLUMN_ATTEMPTS            = "v1/courses/{0}/gradebook/columns/{1}/attempts"
    COURSES                    = "v1/courses"
    COURSE_MEMBERS             = "v1/courses/{0}/users"
    COURSE_GRADE_COLUMNS_USERS = "v1/courses/{0}/gradebook/columns/{1}/users/{2}"
    USERS                      = "v1/users"

    __TEST                     = "rowantest"
    __PROD                     = "rowan"

    def __init__(self, in_app_key, in_app_id, in_secret_key, is_test=False):
        """
        Constructor
        :param in_app_key:    The provided developer application key
        :param in_app_id:     The provided application id
        :param in_secret_key: The provided secret key
        :param is_test:       Whether or not to use the test instance of Blackboard
        """

        url = "https://{0}.blackboard.com/learn/api/public/".format(self.__TEST if is_test else self.__PROD)
        super().__init__(in_public_key=in_app_key, in_private_key=in_secret_key, in_url=url)
        self.app_id = in_app_id
        self.token = self.__get_oauth2_token()
        self._set_endpoints()
        self._set_args_mapping()

    def _set_endpoints(self):
        """
        Sets a list of valid endpoints for this API
        :return: a list of valid endpoints for this API
        """
        self.endpoints = [self.COURSES, self.COLUMNS, self.COLUMN_ATTEMPTS, self.COURSE_MEMBERS,
                          self.COURSE_GRADE_COLUMNS_USERS, self.USERS]

    def _set_args_mapping(self):
        """
        Sets a mapping for each endpoint, specifying valid input parameters.
        :return: A dict containing endpoints as keys and their valid parameters names (list) as values
        """
        self.endpoint_to_args = {
            self.COURSES: ["offset", "limit", "courseId", "name", "description", "externalId", "created", "allowGuests",
                           "createdCompare", "dataSourceId", "termId", "organization", "sort", "fields"],
            self.COLUMNS: ["offset", "limit", "contentId", "fields"],
            self.COLUMN_ATTEMPTS: ["offset", "limit", "userId", "attemptStatuses", "fields"],
            self.COURSE_MEMBERS: ["offset", "limit", "created", "createdCompare", "dataSourceId", "lastAccessed",
                                  "lastAccessedCompare", "availability.available", "sort", "fields"],
            self.COURSE_GRADE_COLUMNS_USERS: ["fields"],
            self.USERS: ["offset", "limit", "userName", "externalId", "created", "createdCompare", "dataSourceId",
                         "name.family", "availability.available", "sort", "fields"]
        }

    def _hit_endpoint(self, valid_args, endpoint_name, get_one=False, request_type="GET", **kwargs):
        """
        Method used to abstract the calling of REST endpoints
        :param valid_args:    A collection of valid parameter names for this endpoint
        :param endpoint_name: The endpoint path after the base url
        :param request_type:  The type of HTTP request being performed
        :param kwargs:        All API parameters are entered as keyword arguments
        :return:
        """
        # only do work if all of the given parameters are valid
        if all(arg in valid_args for arg in kwargs.keys()):

            if self.token.is_expired:
                self.token = self.__get_oauth2_token()

            auth_header = "Bearer {0}".format(self.token.token)
            headers = {"Authorization": auth_header, "Content-Type": "application/json; charset=utf-8"}
            full_url = self.url + endpoint_name
            r_type = request_type.upper()
            if r_type == "GET":
                data = requests.get(full_url, params=kwargs, headers=headers)
            elif r_type == "PUT":
                data = requests.put(full_url, data=kwargs, headers=headers)
            elif r_type == "POST":
                data = requests.post(full_url, data=kwargs, headers=headers)
            else:
                raise Exception("Invalid request type submitted.")

            status = int(data.status_code)
            if 300 >= status >= 200:
                return data.json()
            elif status >= 500:
                raise ApiException("Internal Server Error")
            elif status >= 400:
                try:
                    raise ApiException(responses[status])
                except KeyError:
                    raise ApiException("Error processing request.")
            else:
                raise ApiException("Unknown error.")
        else:
            bad_args = ", ".join(list(kwargs.keys()))
            good_args = ", ".join(valid_args)
            msg = "Invalid parameter supplied at BlackBoardLearn::_hit_endpoint(). Arguments provided: {0}. " \
                  "Valid arguments: {1}.".format(bad_args, good_args)
            raise ParameterException(msg)

    def __get_oauth2_token(self):
        """
        Returns an auth token, refer to https://community.blackboard.com/docs/DOC-1644-authorization-and-authentication
        for more information
        :return:
        """

        body = {"grant_type": "client_credentials"}
        auth_str = base64.b64encode("{0}:{1}".format(self.public_key, self.private_key).encode("ascii"))
        auth = "Basic {0}".format(auth_str.decode("ascii"))
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": auth}
        raw_token = requests.post(self.url + "v1/oauth2/token", data=body, headers=headers)
        status = int(raw_token.status_code)

        if status >= 400:
            if status == 403:
                raise ApiException("Invalid Permissions.")
            else:
                raise ApiException("Error connecting to API.")
        else:
            raw_token = raw_token.json()

        return Token(raw_token["expires_in"], raw_token["access_token"], raw_token["token_type"])

    def get_courses(self, **kwargs):
        """
        Returns a list of courses based on given parameters.
        See documentation for /learn/api/public/v1/courses for more info.

        :param kwargs: any endpoint parameters
        :return:       a list of courses from BlackBoard
        """
        endpoint = self.COURSES
        return self._hit_endpoint(self.endpoint_to_args[endpoint], endpoint, **kwargs)["results"]

    def get_courses_columns(self, course_id, **kwargs):
        """
        Returns a list of gradebook columns for a course
        See documentation for /learn/api/public/v1/{courseId}/gradebook/columns for more info.

        :param course_id: The unique id for the course which's gradebook columns you want
        :param kwargs:    Any other endpoint parameters
        :return:          A list of gradebook columns for the given course id
        """
        endpoint = self.COLUMNS
        return self._hit_endpoint(self.endpoint_to_args[endpoint], endpoint.format(course_id), **kwargs)["results"]

    def get_course_columns_attempts(self, course_id, column_id, **kwargs):
        """
        Returns a list of attempts for a column in a given course's gradebook.
        See /learn/api/public/v1/courses/{courseId}/gradebook/columns/{columnId}/attempts for more info
        :param course_id: The unique course id
        :param column_id: The unique column id
        :return:          The attempts for the given column
        """
        endpoint = self.COLUMN_ATTEMPTS
        return self._hit_endpoint(self.endpoint_to_args[endpoint],
                                  endpoint.format(course_id, column_id), **kwargs)["results"]

    def get_course_members(self, course_id, role=None, **kwargs):
        """
        Returns a list of members for a given course.
        See documentation for /learn/api/public/v1/courses/{courseId}/users for more info

        :param course_id: The unique id for the course which's gradebook columns you want
        :param role:      Filters the list to only include members of the given role
        :param kwargs:    Any other endpoint parameters
        :return:          A list of gradebook columns for the given course id
        """
        endpoint = self.COURSE_MEMBERS
        data = self._hit_endpoint(self.endpoint_to_args[endpoint], endpoint.format(course_id), **kwargs)["results"]
        return list(filter(lambda x: x["courseRoleId"] == role, data)) if role else data

    def get_course_grade_columns_by_user(self, course_id, column_id, user_id, **kwargs):
        """
        Returns a list of gradebook columns for a certain course-column-user id combination
        See /learn/api/public/v1/courses/{courseId}/gradebook/columns/{columnId}/users/{userId} for more info

        :param course_id: The unique id for the course
        :param column_id: The unique id for the gradebook column
        :param user_id:   The unique id for the user within the course
        :param kwargs:    All other endpoint parameters
        :return:          A list of gradebook columns for the course-column-user combination
        """
        endpoint = self.COURSE_GRADE_COLUMNS_USERS
        return self._hit_endpoint(self.endpoint_to_args[endpoint],
                                  endpoint.format(course_id, column_id, user_id), **kwargs)

    def get_users(self, user_id=None, **kwargs):
        """
        Returns a list of users based on given parameters, or a single user if the user_id argument is utilized
        See /learn/api/public/v1/users for more info

        :param user_id: A unique id for a user
        :param kwargs:  All other endpoint parameters
        :return:        A list of users based on the input parameters
        """
        endpoint = self.USERS
        valid_args = self.endpoint_to_args[endpoint]
        if user_id:
            endpoint += "/{0}".format(user_id)
            valid_args = ("fields", )
        return self._hit_endpoint(valid_args, endpoint, **kwargs)