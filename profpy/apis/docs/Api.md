# profpy Parent API Class
The profpy.apis.Api class is the parent class from which all new API-wrapper classes descend from. Any new wrapper must be a 
child of this class, and must implement its abstract methods.

## Basic Usage
Here is an example of a new class being made using the Api parent. This is very basic but it gives a general idea of how to get started. 
Check out the wrapper classes for more detailed examples. 
```python
import requests
from profpy.apis import Api, ParameterException, ApiException


class PhoneApi(Api):

    # define endpoints
    GET_NUMBERS   = "/phone_numbers/"
    GET_AREA_CODES = "/area_codes/"
    
    # constructor
    def __init__(self, url, public_key, private_key):
        
        # call parent's constructor
        super().__init__(in_public_key=public_key, in_private_key=private_key, in_url=url)
        
        # any additional properties can be defined here
    
    # implement abstract methods
    def _set_args_mapping(self):
        """
        Defines valid query parameters for the endpoint
        """
        self.endpoint_to_args = {
            self.GET_NUMBERS: ["first_name", "last_name", "limit", "area_code"],
            self.GET_AREA_CODES: ["state", "code"]
        }
    
    def _set_endpoints(self):
        """
        Defines list of valid endpoints
        """
        self.endpoints = [self.GET_NUMBERS, self.GET_AREA_CODES]
    
    def _hit_endpoint(self, valid_args, endpoint_name, get_one=False, request_type="GET", **kwargs):
        """
        Abstracts the logic for hitting endpoints. This is a very basic example with minimal exception handling 
        and minimal request type support.
        """
        if all(arg in valid_args for arg in kwargs):
            full_url = self.url + endpoint_name
            headers = {"Content-Type": "application/json; charset=utf-8", "Accept": "application/json"}
            data = requests.get(full_url, params=kwargs, headers=headers)
            if 200 <= data.status_code < 300:
                return data.content
            else:
                raise ApiException(data.text, data.status_code)
        else:
            raise ParameterException("Invalid query parameters.")
        
    # define actual public methods for hitting endpoints
    def get_phone_numbers(self, **kwargs):
        endpoint = self.GET_NUMBERS
        return self._hit_endpoint(self.endpoint_to_args[endpoint], endpoint, **kwargs)
        
    def get_area_codes(self, **kwargs):
        endpoint = self.GET_AREA_CODES
        return self._hit_endpoint(self.endpoint_to_args[endpoint], endpoint, **kwargs)
```

# Technical Documentation 
## Constructor
### profpy.apis.Api( *in_public_key, in_private_key, in_url, in_ip_restriction=None* ) 
Returns an Api object.

Parent Class: [object](https://docs.python.org/3.7/library/functions.html?#object)

Parameters:

| Name        | Description                                        | Type          | Required | Default |
|-------------|----------------------------------------------------|---------------|----------|---------|
| in_public_key  | public api key | str          | yes       |    |
| in_private_key | private/secret api key | str | yes | |
| in_url | the API instance's url | str | yes |  |
| in_ip_restriction | the ip address that these keys are restricted to access the api from | str | no | None |

---
## Properties

### public key
The public API key 

### private key
The private/secret API key 

### url 
The base API url for all endpoints 

### ip_restriction
The ip address that these credentials can make requests from 

### endpoints
A list of this API's endpoints

### endpoint_to_args
A dict that maps endpoints to their valid query parameters

### uuid, time, hash, token
These properties are used for authentication purposes. They are set/utilized (if at all) differently across various APIs. 

--- 

## Abstract Methods

### _set_args_mapping
Sets the endpoint-to-parameters map property. 

### _set_endpoints
Sets the endpoint list property.

### _hit_endpoint 
Defines any abstracted logic for hitting endpoints for this API. 

