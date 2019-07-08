import base64
import json
import requests
from http.client import responses
from . import Api, ApiException, ParameterException, Token


class BlackBoardLearn(Api):
    """
    Class that optimizes http calls to the BlackBoard REST interface

    Documentation regarding individual endpoints can be found at:
    https://developer.blackboard.com/portal/displayApi
    """

    COLUMNS = "v1/courses/{0}/gradebook/columns"
    COLUMN_ATTEMPTS = "v1/courses/{0}/gradebook/columns/{1}/attempts"
    COURSES = "v1/courses"
    COURSE = "v1/courses/{0}"
    COURSE_GROUP = "v1/courses/{0}/groups/{1}"
    COURSE_GROUPS = "v1/courses/{0}/groups"
    COURSE_MEMBERS = "v1/courses/{0}/users"
    COURSE_MEMBERSHIP = "v1/courses/{0}/users/{1}"
    COURSE_GRADE_COLUMNS_USERS = "v1/courses/{0}/gradebook/columns/{1}/users/{2}"
    COURSE_ROLES = "v1/courseRoles"
    USERS = "v1/users"
    USER = "v1/users/{0}"

    __REQUEST_FUNCTIONS = {
        "GET": requests.get,
        "POST": requests.post,
        "PUT": requests.put,
        "PATCH": requests.patch,
        "DELETE": requests.delete,
    }

    def __init__(self, in_app_key, in_app_id, in_secret_key, in_url):
        """
        Constructor
        :param in_app_key:    The provided developer application key
        :param in_app_id:     The provided application id
        :param in_secret_key: The provided secret key
        :param in_url:        The url for this API
        """

        super().__init__(
            in_public_key=in_app_key, in_private_key=in_secret_key, in_url=in_url
        )
        self.app_id = in_app_id
        self.token = self.__get_oauth2_token()
        self._set_endpoints()
        self._set_args_mapping()

    def _set_endpoints(self):
        """
        Sets a list of valid endpoints for this API
        :return: a list of valid endpoints for this API
        """
        self.endpoints = [
            self.COURSES,
            self.COLUMNS,
            self.COLUMN_ATTEMPTS,
            self.COURSE_MEMBERS,
            self.COURSE_GRADE_COLUMNS_USERS,
            self.USERS,
        ]

    def _set_args_mapping(self):
        """
        Sets a mapping for each endpoint, specifying valid input parameters.
        :return: A dict containing endpoints as keys and their valid parameters names (list) as values
        """
        self.endpoint_to_args = {
            "GET": {
                self.COURSE: ["fields"],
                self.COURSES: [
                    "offset",
                    "limit",
                    "courseId",
                    "name",
                    "description",
                    "externalId",
                    "created",
                    "allowGuests",
                    "createdCompare",
                    "dataSourceId",
                    "termId",
                    "organization",
                    "sort",
                    "fields",
                ],
                self.COURSE_ROLES: [
                    "offset",
                    "limit",
                    "sort",
                    "custom",
                    "roleId",
                    "fields",
                ],
                self.COLUMNS: ["offset", "limit", "contentId", "fields"],
                self.COLUMN_ATTEMPTS: [
                    "offset",
                    "limit",
                    "userId",
                    "attemptStatuses",
                    "fields",
                ],
                self.COURSE_MEMBERS: [
                    "offset",
                    "limit",
                    "created",
                    "createdCompare",
                    "dataSourceId",
                    "lastAccessed",
                    "lastAccessedCompare",
                    "availability.available",
                    "sort",
                    "fields",
                ],
                self.COURSE_GRADE_COLUMNS_USERS: ["fields"],
                self.USERS: [
                    "offset",
                    "limit",
                    "userName",
                    "externalId",
                    "created",
                    "createdCompare",
                    "dataSourceId",
                    "name.family",
                    "availability.available",
                    "sort",
                    "fields",
                ],
                self.USER: ["fields"],
                self.COURSE_GROUP: ["fields"],
                self.COURSE_GROUPS: ["offset", "limit", "sort", "fields"],
            },
            "POST": {
                self.USERS: [
                    "dataSourceId",
                    "gender",
                    "externalId",
                    "created",
                    "institutionRoleIds",
                    "name",
                    "birthDate",
                    "lastLogin",
                    "address",
                    "userName",
                    "locale",
                    "id",
                    "educationLevel",
                    "job",
                    "contact",
                    "systemRoleIds",
                    "studentId",
                    "uuid",
                    "password",
                    "availability",
                ]
            },
            "DELETE": {self.USER: [], self.COURSE_MEMBERSHIP: []},
            "PATCH": {self.COURSE_MEMBERSHIP: []},
            "PUT": {self.COURSE_MEMBERSHIP: []},
        }

    def _hit_endpoint(
        self, valid_args, endpoint_name, get_one=False, request_type="GET", **kwargs
    ):
        """
        Method used to abstract the calling of REST endpoints
        :param valid_args:    A collection of valid parameter names for this endpoint
        :param endpoint_name: The endpoint path after the base url
        :param request_type:  The type of HTTP request being performed
        :param kwargs:        All API parameters are entered as keyword arguments
        :return:
        """
        # only do work if all of the given parameters are valid
        if all(arg in valid_args for arg in kwargs.keys()) or not valid_args:

            if self.token.is_expired:
                self.token = self.__get_oauth2_token()

            auth_header = "Bearer {0}".format(self.token.token)
            headers = {
                "Authorization": auth_header,
                "Content-Type": "application/json; charset=utf-8",
            }
            full_url = self.url + endpoint_name
            r_type = request_type.upper()

            try:
                request_function = self.__REQUEST_FUNCTIONS[r_type]
                if r_type == "GET":
                    data = request_function(full_url, params=kwargs, headers=headers)
                else:
                    in_data = (
                        json.dumps(kwargs)
                        if r_type in ["POST", "PATCH", "PUT"]
                        else kwargs
                    )
                    data = request_function(full_url, data=in_data, headers=headers)
            except KeyError:
                raise Exception("Invalid request type submitted.")

            status = int(data.status_code)
            if 300 >= status >= 200:
                if status == 204:
                    return None
                else:
                    return data.json()
            elif status >= 500:
                raise ApiException("Internal Server Error", status)
            elif status >= 400:
                try:
                    try:
                        message = data.json()["message"]
                    except KeyError:
                        message = responses[status]
                    raise ApiException(message, status)
                except KeyError:
                    raise ApiException("Error processing request.", status)
            else:
                raise ApiException("Unknown error.", status)
        else:
            bad_args = ", ".join(list(kwargs.keys()))
            good_args = ", ".join(valid_args)
            msg = (
                "Invalid parameter supplied at BlackBoardLearn::_hit_endpoint(). Arguments provided: {0}. "
                "Valid arguments: {1}.".format(bad_args, good_args)
            )
            raise ParameterException(msg)

    def __get_oauth2_token(self):
        """
        Returns an auth token, refer to https://community.blackboard.com/docs/DOC-1644-authorization-and-authentication
        for more information
        :return:
        """

        body = {"grant_type": "client_credentials"}
        auth_str = base64.b64encode(
            "{0}:{1}".format(self.public_key, self.private_key).encode("ascii")
        )
        auth = "Basic {0}".format(auth_str.decode("ascii"))
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": auth,
        }
        raw_token = requests.post(
            self.url + "v1/oauth2/token", data=body, headers=headers
        )
        status = int(raw_token.status_code)

        if status >= 400:
            if status == 403:
                raise ApiException("Invalid Permissions.", status)
            else:
                raise ApiException("Error connecting to API.", status)
        else:
            raw_token = raw_token.json()

        return Token(
            raw_token["expires_in"], raw_token["access_token"], raw_token["token_type"]
        )

    def __get_valid_roles(self):
        """
        :return: any valid user roles in the BlackBoard system
        """
        return [role["roleId"] for role in self.get_course_roles()]

    def get_course(self, course_id, use_blackboard_course_id=False):
        """
        Returns a course based on the given course id.
        :param course_id:                This id of the course    (str)
        :param use_blackboard_course_id: Whether or not to use the internal BlackBoard id for the course (bool)
        :return:                         A course from BlackBoard (dict)
        """
        endpoint = self.COURSE
        valid_args = self.endpoint_to_args["GET"][endpoint]
        endpoint = endpoint.format(
            course_id if use_blackboard_course_id else "courseId:{0}".format(course_id)
        )
        return self._hit_endpoint(valid_args, endpoint)

    def get_courses(self, **kwargs):
        """
        Returns a list of courses based on given parameters.
        See documentation for /learn/api/public/v1/courses for more info.

        :param kwargs: any endpoint parameters
        :return:       a list of courses from BlackBoard
        """
        endpoint = self.COURSES
        return self._hit_endpoint(
            self.endpoint_to_args["GET"][endpoint], endpoint, **kwargs
        )["results"]

    def get_courses_columns(self, course_id, use_blackboard_course_id=False, **kwargs):
        """
        Returns a list of gradebook columns for a course
        See documentation for /learn/api/public/v1/{courseId}/gradebook/columns for more info.

        :param course_id:                The unique id for the course which's gradebook columns you want
        :param use_blackboard_course_id: Whether or not to use the internal BlackBoard id for the course
        :param kwargs:                   Any other endpoint parameters
        :return:                         A list of gradebook columns for the given course id
        """
        endpoint = self.COLUMNS
        valid_args = self.endpoint_to_args["GET"][endpoint]
        endpoint = endpoint.format(
            course_id if use_blackboard_course_id else "courseId:{0}".format(course_id)
        )
        return self._hit_endpoint(valid_args, endpoint, **kwargs)["results"]

    def get_course_columns_attempts(
        self,
        course_id,
        column_id,
        use_blackboard_course_id=False,
        use_blackboard_column_id=False,
        **kwargs
    ):
        """
        Returns a list of attempts for a column in a given course's gradebook.
        See /learn/api/public/v1/courses/{courseId}/gradebook/columns/{columnId}/attempts for more info
        :param course_id:                The unique course id
        :param column_id:                The unique column id
        :param use_blackboard_course_id: Whether or not to use the internal BlackBoard id for the course
        :param use_blackboard_column_id: Whether or not to use the internal BlackBoard id for the course column
        :param kwargs:                   Other endpoint parameters
        :return:                         The attempts for the given column
        """
        endpoint = self.COLUMN_ATTEMPTS
        valid_args = self.endpoint_to_args["GET"][endpoint]
        course_param = (
            course_id if use_blackboard_course_id else "courseId:{0}".format(course_id)
        )
        col_param = (
            column_id
            if use_blackboard_column_id
            else "externalId:{0}".format(column_id)
        )
        return self._hit_endpoint(
            valid_args, endpoint.format(course_param, col_param), **kwargs
        )["results"]

    def get_course_members(
        self, course_id, role=None, use_blackboard_course_id=False, **kwargs
    ):
        """
        Returns a list of members for a given course.
        See documentation for /learn/api/public/v1/courses/{courseId}/users for more info

        :param course_id:                The unique id for the course which's gradebook columns you want
        :param role:                     Filters the list to only include members of the given role
        :param use_blackboard_course_id: Whether or not to use the internal BlackBoard id for the course
        :param kwargs:                   Any other endpoint parameters
        :return:                         A list of gradebook columns for the given course id
        """
        endpoint = self.COURSE_MEMBERS
        valid_args = self.endpoint_to_args["GET"][endpoint]
        endpoint = endpoint.format(
            course_id
            if use_blackboard_course_id
            else "externalId:{0}".format(course_id)
        )
        data = self._hit_endpoint(valid_args, endpoint, **kwargs)["results"]
        return list(filter(lambda x: x["courseRoleId"] == role, data)) if role else data

    def get_course_grade_columns_by_user(
        self,
        course_id,
        column_id,
        user_id,
        use_blackboard_course_id=False,
        use_blackboard_column_id=False,
        use_blackboard_user_id=False,
        **kwargs
    ):
        """
        Returns a list of gradebook columns for a certain course-column-user id combination
        See /learn/api/public/v1/courses/{courseId}/gradebook/columns/{columnId}/users/{userId} for more info

        :param course_id:                The unique id for the course
        :param column_id:                The unique id for the gradebook column
        :param user_id:                  The unique id for the user within the course
        :param use_blackboard_course_id: Whether or not to use the internal BlackBoard id for the course
        :param use_blackboard_column_id: Whether or not to use the internal BlackBoard id for the course column
        :param use_blackboard_user_id:   Whether or not to use the internal BlackBoard id for the user
        :param kwargs:                   All other endpoint parameters
        :return:                         A list of gradebook columns for the course-column-user combination
        """
        endpoint = self.COURSE_GRADE_COLUMNS_USERS
        valid_args = self.endpoint_to_args["GET"][endpoint]
        course_param = (
            course_id if use_blackboard_course_id else "courseId:{0}".format(course_id)
        )
        column_param = (
            column_id
            if use_blackboard_column_id
            else "externalId:{0}".format(column_id)
        )
        user_param = (
            user_id if use_blackboard_user_id else "externalId:{0}".format(user_id)
        )
        endpoint = endpoint.format(course_param, column_param, user_param)
        return self._hit_endpoint(valid_args, endpoint, **kwargs)

    def get_course_group(
        self,
        course_id,
        group_id,
        use_blackboard_course_id=False,
        use_blackboard_group_id=False,
    ):
        """
        Returns a group object for the specified course id and group id
        :param course_id:                The course id
        :param group_id:                 The group id
        :param use_blackboard_course_id: Whether or not to use the internal BlackBoard id for the course
        :param use_blackboard_group_id:  Whether or not to use the internal BlackBoard id for the group
        :return:                         The group object
        """
        endpoint = self.COURSE_GROUP
        valid_args = self.endpoint_to_args["GET"][endpoint]
        course_param = (
            course_id if use_blackboard_course_id else "courseId:{0}".format(course_id)
        )
        group_param = (
            group_id if use_blackboard_group_id else "externalId:{0}".format(group_id)
        )
        return self._hit_endpoint(
            valid_args, endpoint.format(course_param, group_param)
        )

    def get_course_groups(self, course_id, use_blackboard_course_id=False):
        """
        Returns a list of group objects for the specified course
        :param course_id:                The course id
        :param use_blackboard_course_id: Whether or not to use the internal BlackBoard id for the course
        :return:                         The list of course group objects
        """
        endpoint = self.COURSE_GROUPS
        valid_args = self.endpoint_to_args["GET"][endpoint]
        endpoint = endpoint.format(
            course_id if use_blackboard_course_id else "courseId:{0}".format(course_id)
        )
        return self._hit_endpoint(valid_args, endpoint)["results"]

    def get_course_roles(self, **kwargs):
        """
        Returns a list of course roles.
        :param kwargs: Endpoint parameters
        :return:       A list of course roles
        """
        endpoint = self.COURSE_ROLES
        valid_args = self.endpoint_to_args["GET"][endpoint]
        return self._hit_endpoint(valid_args, endpoint, **kwargs)["results"]

    def get_user(self, user_id, use_blackboard_user_id=False):
        """
        Returns a user based on the given user id
        :param user_id:                  The banner id of the user (str)
        :param use_blackboard_user_id:   Whether or not to use the internal BlackBoard id for the user
        :return:                         The found user            (dict)
        """
        endpoint = self.USER
        valid_args = self.endpoint_to_args["GET"][endpoint]
        endpoint = endpoint.format(
            user_id if use_blackboard_user_id else "externalId:{0}".format(user_id)
        )
        return self._hit_endpoint(valid_args, endpoint)

    def get_users(self, **kwargs):
        """
        Returns a list of users based on given parameters, or a single user if the user_id argument is utilized
        See /learn/api/public/v1/users for more info

        :param kwargs:  All endpoint parameters
        :return:        A list of users based on the input parameters
        """
        endpoint = self.USERS
        valid_args = self.endpoint_to_args["GET"][endpoint]
        return self._hit_endpoint(valid_args, endpoint, **kwargs)["results"]

    def create_user(self, in_json):
        """
        Creates a user in BlackBoard based on input JSON
        :param in_json: Input data for the new user (dict)
        :return:        The response                (requests.Response)
        """
        endpoint = self.USERS
        valid_args = self.endpoint_to_args["POST"][endpoint]
        return self._hit_endpoint(valid_args, endpoint, request_type="POST", **in_json)

    def delete_user(self, user_id):
        """
        Deletes a user in Blackboard based on user_id
        This user id can be the primary system id or a secondary id (externalId, userName, uuid) prefixed by type.
        Ex) api.delete_user(user_id="userName:johnsmith3")

        :param user_id: The input user id (str)
        :return:
        """
        endpoint = self.USER
        valid_args = self.endpoint_to_args["DELETE"][endpoint]
        endpoint = endpoint.format(user_id)
        return self._hit_endpoint(valid_args, endpoint, request_type="DELETE")

    def add_user_to_course(
        self,
        user_id,
        course_id,
        role="Student",
        use_blackboard_user_id=False,
        use_blackboard_course_id=False,
    ):
        """
        Enrolls a user into a course
        Valid roles: Student, Instructor, TeachingAssistant, CourseBuilder, Grader, Guest

        :param user_id:                  User's banner id                          (str)
        :param course_id:                The course id                             (str)
        :param role:                     The role the user will have in the course (str)
        :param use_blackboard_user_id:   Whether or not to use the internal BlackBoard id for the user
        :param use_blackboard_course_id: Whether or not to use the internal BlackBoard id for the course
        :return:
        """
        valid_roles = self.__get_valid_roles()
        if role not in valid_roles:
            raise ParameterException(
                'Invalid role: "{0}". Valid roles: {1}'.format(
                    role, ", ".join(valid_roles)
                )
            )

        endpoint = self.COURSE_MEMBERSHIP
        valid_args = self.endpoint_to_args["PUT"][endpoint]
        course_param = (
            course_id if use_blackboard_course_id else "courseId:{0}".format(course_id)
        )
        user_param = (
            user_id if use_blackboard_user_id else "externalId:{0}".format(user_id)
        )
        endpoint = endpoint.format(course_param, user_param)
        return self._hit_endpoint(
            valid_args, endpoint, request_type="PUT", **dict(courseRoleId=role)
        )

    def update_course_membership(
        self,
        user_id,
        course_id,
        in_json,
        use_blackboard_user_id=False,
        use_blackboard_course_id=False,
    ):
        """
        Updates a user's course membership with a PATCH request
        :param user_id:                  The user's banner id
        :param course_id:                The course id
        :param in_json:                  Other input data
        :param use_blackboard_user_id:   Whether or not to use the internal BlackBoard id for the user
        :param use_blackboard_course_id: Whether or not to use the internal BlackBoard id for the course
        :return:
        """
        endpoint = self.COURSE_MEMBERSHIP
        valid_roles = self.endpoint_to_args["PATCH"][endpoint]
        course_param = (
            course_id if use_blackboard_course_id else "courseId:{0}".format(course_id)
        )
        user_param = (
            user_id if use_blackboard_user_id else "externalId:{0}".format(user_id)
        )
        endpoint = endpoint.format(course_param, user_param)
        return self._hit_endpoint(
            valid_roles, endpoint, request_type="PATCH", **in_json
        )

    def remove_user_from_course(
        self,
        user_id,
        course_id,
        use_blackboard_user_id=False,
        use_blackboard_course_id=False,
    ):
        """
        Removes a user from a course
        :param user_id:                  User's banner id (str)
        :param course_id:                The course id    (str)
        :param use_blackboard_user_id:   Whether or not to use the internal BlackBoard id for the user
        :param use_blackboard_course_id: Whether or not to use the internal BlackBoard id for the course
        :return:
        """
        endpoint = self.COURSE_MEMBERSHIP
        valid_args = self.endpoint_to_args["DELETE"][endpoint]
        course_param = (
            course_id if use_blackboard_course_id else "courseId:{0}".format(course_id)
        )
        user_param = (
            user_id if use_blackboard_user_id else "externalId:{0}".format(user_id)
        )
        return self._hit_endpoint(
            valid_args, endpoint.format(course_param, user_param), request_type="DELETE"
        )
