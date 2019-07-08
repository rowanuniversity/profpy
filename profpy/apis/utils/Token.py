import datetime


class Token(object):
    """
    Class that handles Oauth2 Tokens
    """

    def __init__(self, expires_in_seconds, in_token_id, in_token_type):
        """
        Constructor
        :param expires_in_seconds: The number of seconds from now in which the token expires
        :param in_token_id:        The token's unique id
        :param in_token_type:      The token's type
        """
        self.token = in_token_id
        self.expire_time = datetime.datetime.now() + datetime.timedelta(
            0, expires_in_seconds
        )
        self.type = in_token_type

    @property
    def is_expired(self):
        """
        :return: Whether or not the token is expired
        """
        return datetime.datetime.now() > self.expire_time

    @property
    def header(self):
        return {
            "Authorization": "Bearer {0}".format(self.token),
            "Content-Type": "application/json; charset=utf-8",
        }
