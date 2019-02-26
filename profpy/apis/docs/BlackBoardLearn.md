# BlackBoard Learn API
An API wrapper to optimize calls to the BlackBoard Learn API. This class can be used to add/remove users and manage courses, course memberships, groups, etc.

## Basic Usage
This API is instantiated using developer keys in its constructor. These keys include an application ID, a public API key, and a secret key. 
```python
from profpy.apis import BlackBoardLearn
api = BlackBoardLearn(in_app_id="app_id", in_app_key="api_key", in_secret_key="secret_key", in_url="this-blackboard-api.com")
```

#### Retrieving data
There are many functions available for use. Most deal with users, courses, and memberships. 
```python
from profpy.apis import BlackBoardLearn
api = BlackBoardLearn(in_app_id="app_id", in_app_key="api_key", in_secret_key="secret_key", in_url="this-blackboard-api.com")

# grab all users
users = api.get_users()

# grab one user by banner id
user = api.get_user(user_id="in_banner_id")

# grab users by other api query parameters (if using nested parameters such as name.family, use the **{ } convention)
users = api.get_users(userName="in_username")
users = api.get_users(**{"name.family": "in_last_name"})
```

```python
from profpy.apis import BlackBoardLearn
api = BlackBoardLearn(in_app_id="app_id", in_app_key="api_key", in_secret_key="secret_key", in_url="this-blackboard-api.com")

# get all courses
courses = api.get_courses()

# get one course based on id
course = api.get_course(course_id="in_id")
```

#### Inserting/Updating Data
```python
from profpy.apis import BlackBoardLearn
api = BlackBoardLearn(in_app_id="app_id", in_app_key="api_key", in_secret_key="secret_key", in_url="this-blackboard-api.com")

# create user
in_user_data = {
    "userName": "test_user_name",
    "studentId": "test_student_id",
    "externalId": "test_external_id",
    "password": "",
    "name": {
        "given": "Dennis",
        "family": "Nedry"
    }
}
api.create_user(in_user_data)

# enroll a user in a course, default role is student
api.add_user_to_course(course_id="in_course_id", user_id="in_banner_id")

# as an instructor
api.add_user_to_course(course_id="in_course_id", user_id="in_banner_id", role="Instructor")
```

# Technical Documentation
##  Constructor
### profpy.apis.BlackBoardLearn( *in_app_key, in_app_id, in_secret_key, is_test=False* )
Returns an API handler for the 25Live API

Parent Class: [profpy.apis.Api](./Api.md)

Parameters: 

| Name        | Description                                        | Type          | Required | Default |
|-------------|----------------------------------------------------|---------------|----------|---------|
| in_app_key  | public api key | str          | yes       |    |
| in_app_id   | public app id    | str | yes       |      |
| in_secret_key | private api key | str | yes | |
| in_url | the API instance's url | str | yes |  |

Example:
```python
from profpy.apis import BlackBoardLearn
api = BlackBoardLearn("api_public_key", "app_id", "api_secret_key", "this-blackboard-api.com")
```

---

## Properties
#### app_id (str)
The app id used to connect to this api. 

#### token (profpy.apis.utils.Token)
The Oauth token used to make calls to the api

---

## Methods
Note: "user_id" is equivalent to "banner id" for the purposes of this API. Anytime a method takes keyword arguments
as an input parameter can take in any valid query parameter for the corresponding endpoint listed on the API documentation site.

**All endpoints and their corresponding documentation can be found at <a href='https://developer.blackboard.com/portal/displayApi'>https://developer.blackboard.com/portal/displayApi</a>**. Each method below will specify the
endpoint it matches up with in the previously provided link. 

Note: Any optional method input parameters such as "use_blackboard_\<object\>_id" are referring to BlackBoard's internal 
primary keys. For instance, users may be identified by an organization one way (school id, ssn, etc.) that is stored as an
"externalId" in each record. By default, user-related functions search on this field. However, if ```use_blackboard_user_id``` is
set to ```True```, then the method will search on the primary BlackBoard key (often comprised of numbers and underscores).


### get_course( *course_id, use_blackboard_course_id=False*)
Returns a course based on the given course id.

Endpoint: GET /learn/api/v1/courses/{courseId}

### get_courses( *\*\*kwargs* )
Returns a list of courses based on the given query parameters.

Endpoint: GET /learn/api/v1/courses

### get_course_columns( *course_id, use_blackboard_course_id=False, \*\*kwargs* )
Returns course gradebook columns based on the course id and any query parameters.

Endpoint: GET /learn/api/public/v1/courses/{courseId}/gradebook/columns

### get_course_columns_attempts( *course_id, column_id, use_blackboard_course_id=False, use_blackboard_column_id=False, \*\*kwargs* )
Returns a list of attempts on a gradebook column based on course id, column id, and query parameters.

Endpoint: GET /learn/api/public/v1/courses/{courseId}/gradebook/columns/{columnId}/attempts

### get_course_members( *course_id, role=None, use_blackboard_course_id=False, \*\*kwargs* )
Returns a list of users of a course based on course id and query parameters (and optionally a specified role)

Endpoint: GET /learn/api/public/v1/courses/{courseId}/users

### get_course_grade_columns_by_user( *course_id, column_id, user_id, use_blackboard_course_id=False, use_blackboard_column_id=False, use_blackboard_user_id=False, \*\*kwargs* )
Returns a list of gradebook columns for a certain course-column-user id combination

Endpoint: GET /learn/api/public/v1/courses/{courseId}/gradebook/columns/{columnId}/users/{userId}

### get_course_group( *course_id, group_id, use_blackboard_course_id=False, use_blackboard_group_id=False* )
Returns a course group based on course id and group id

Endpoint: GET /learn/api/public/v1/courses/{courseId}/groups/{groupId}

### get_course_groups( *course_id, use_blackboard_course_id=False* )
Returns a list of course groups for the given course id.

Endpoint: GET /learn/api/public/v1/courses/{courseId}/groups

### get_course_roles( *\*\*kwargs* )
Returns a list of course roles based on the given query parameters.

Endpoint: GET /learn/api/public/v1/courseRoles

### get_user( *user_id, use_blackboard_user_id=False* )
Returns a user based on the given user id 

Endpoint: GET /learn/api/public/v1/users/{userId}

### get_users( *\*\*kwargs* ) 
Returns a list of users based on query parameters

Endpoint: GET /learn/api/public/v1/users

### create_user( *in_json* )
Creates a user based on input json data. See corresponding documentation for more info. 

Endpoint: POST /learn/api/public/v1/users

### delete_user( *user_id, use_blackboard_user_id=False* )
Deletes a user based on given user id.

Endpoint: DELETE /learn/api/public/v1/users/{userId}

### add_user_to_course( *user_id, course_id, role="Student", use_blackboard_user_id=False,  use_blackboard_course_id=False* )
Enrolls a user in a course based on the given user and course ids. Optionally, the caller can provide a role (defaults to "Student").

Endpoint: PUT /learn/api/public/v1/courses/{courseId}/users/{userId}

### update_course_membership( *user_id, course_id, in_json, use_blackboard_user_id=False, use_blackboard_course_id=False* )
Updates a course membership with the given user and course ids, and the given input json.

Endpoint: PATCH /learn/api/public/courses/{courseId}/users/{userId}

### remove_user_from_course( *user_id, course_id, use_blackboard_user_id=False, use_blackboard_course_id=False* )
Removes a user from a course based on user and course ids.

Endpoint: DELETE /learn/api/public/courses/{courseId}/users/{userId}
