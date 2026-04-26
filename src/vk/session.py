import getpass
import logging
import urllib
from json import loads
from re import search

import requests

from .api import APINamespace
from .exceptions import ErrorCodes, VkAPIError, VkAuthError
from .utils import stringify

logger = logging.getLogger(__name__)


class APIBase:
    METHOD_COMMON_PARAMS = {'v', 'lang', 'https', 'test_mode'}

    API_URL = 'https://api.vk.ru/method/'

    def __new__(cls, *args, **kwargs):
        method_common_params = {
            key: kwargs.pop(key)
            for key in tuple(kwargs) if key in cls.METHOD_COMMON_PARAMS
        }

        api = object.__new__(cls)
        api.__init__(*args, **kwargs)

        return APINamespace(api, method_common_params)

    def __init__(self, timeout=10, proxy=None):
        self.timeout = timeout

        self.session = requests.Session()
        self.session.proxies = {'http': proxy, 'https': proxy}
        self.session.headers['Accept'] = 'application/json'
        self.session.headers['Content-Type'] = 'application/x-www-form-urlencoded'

    def send(self, request):

        pass

    def prepare_request(self, request):  # noqa: U100
        pass

    def handle_api_error(self, request):
        pass

    def on_api_error(self, request):
        """Default API error handler that handles all errros and raises them. You can add a
        handler for a specific error by redefining it in your class and appending the error
        code to the method name. In this case, the redefined method will be called instead of
        :meth:`on_api_error`. The :exc:`vk.exceptions.VkAPIError` object can be obtained via
        ``request.api_error``

        Args:
            request (vk.api.APIRequest): API request object

        Example:
            .. code-block:: python

                import vk

                class API(vk.APIBase):
                    def on_api_error_1(self, request):
                        print('An unknown error has occurred :(')

                api = API()
        """
        raise request.api_error


class API(APIBase):
    """The simplest VK API implementation. Can process `any API method <https://dev.vk.ru/method>`__
    that can be called from the server

    Args:
        access_token (Optional[str]): Access token for API requests obtained by any means
            (see :ref:`documentation <Getting access>`). Optional when using :class:`InteractiveMixin`
        **kwargs (any): Additional parameters, which will be passed to each request.
            The most useful is `v` - API version and `lang` - language of responses
            (see :ref:`documentation <Making API request>`)

    Example:
        .. code-block:: python

            >>> import vk
            >>> api = vk.API(access_token='...', v='5.131')
            >>> print(api.users.get(user_ids=1))
            [{'id': 1, 'first_name': 'ÐŸÐ°Ð²ÐµÐ»', 'last_name': 'Ð”ÑƒÑ€Ð¾Ð²', ... }]
    """

    def __init__(self, access_token=None, **kwargs):
        super().__init__(**kwargs)
        self.access_token = access_token

    def get_captcha_key(self, api_error):
        """Callback to retrieve CAPTCHA key. Default behavior is to raise exception,
        redefine in a subclass

        Args:
            api_error (vk.exceptions.VkAPIError): Captcha error that occurred

        Returns:
            Captcha solution (a short string consisting of lowercase letters and numbers)
        """
        raise api_error

    def on_api_error_14(self, request):
        """Captcha error handler. Retrieves captcha via :meth:`API.get_captcha_key` and
        resends request
        """
        pass

    def prepare_request(self, request):
        pass


class UserAPI(API):
    """Subclass of :class:`vk.session.API`. It differs only in that it can get access token
    using user credentials (`Implicit flow authorization
    <https://dev.vk.ru/api/access-token/implicit-flow-user>`__).

    Warning:
        This implementation uses the web version of VK to log in and receive cookies, and then
        obtains an access token through Implicit flow authorization. In the future, VK may change
        the approach to authorization (for example, replace it with `VK ID <https://id.vk.ru>`__)
        and maintaining operability will become quite a difficult task, and most likely it will
        be **deprecated**. Use :class:`vk.session.DirectUserAPI` instead

    Args:
        user_login (Optional[str]): User login, optional when using :class:`InteractiveMixin`
        user_password (Optional[str]): User password, optional when using :class:`InteractiveMixin`
        client_id (Optional[int]): ID of the application to authorize with, defaults to
            "VK Admin" app ID
        scope (Optional[Union[str, int]]): Access rights you need. Can be passed
            comma-separated list of scopes, or bitmask sum all of them (see `official
            documentation <https://dev.vk.ru/reference/access-rights>`__). Defaults
            to 'offline'
        **kwargs (any): Additional parameters, which will be passed to each request.
            The most useful is `v` - API version and `lang` - language of responses
            (see :ref:`documentation <Making API request>`)

    Example:
        .. code-block:: python

            >>> import vk
            >>> api = vk.UserAPI(
            ...     user_login='...',
            ...     user_password='...',
            ...     scope='offline,wall',
            ...     v='5.131'
            ... )
            >>> print(api.users.get(user_ids=1))
            [{'id': 1, 'first_name': 'ÐŸÐ°Ð²ÐµÐ»', 'last_name': 'Ð”ÑƒÑ€Ð¾Ð²', ... }]
    """
    LOGIN_URL = 'https://oauth.vk.ru'
    AUTHORIZE_URL = 'https://oauth.vk.ru/authorize'

    def __init__(self, user_login=None, user_password=None, client_id=6121396, scope='offline', **kwargs):
        self.user_login = user_login
        self.user_password = user_password
        self.client_id = client_id
        self.scope = scope

        super().__init__(self.get_access_token(), **kwargs)

    @staticmethod
    def _get_form_action(response):
        pass

    @staticmethod
    def _get_input_value(response, name):
        pass

    @staticmethod
    def _get_captcha_src(response):
        pass

    @staticmethod
    def _get_url_queries(url):
        pass

    @staticmethod
    def _oauth_is_request_success(response):
        pass

    def get_access_token(self):
        pass

    def get_login_form_data(self, response):
        pass

    def login(self, auth_session, login_response=None):
        pass

    def _get_auth_captcha_data(self, response):
        # Return captcha data
        pass

    def _get_auth_captcha_error(self, captcha_sid, captcha_img):
        # Create a bogus error
        pass

    def auth_captcha_is_needed(self, auth_session, response):
        # Get login form action
        pass

    def get_auth_check_code(self):
        """Callback to retrieve authentication check code (if account supports 2FA). Default
        behavior is to raise exception, redefine in a subclass

        Returns:
            The authentication check code can be obtained in the sent SMS, using Google
            Authenticator (or another authenticator), or it can be one of ten backup codes
        """
        raise NotImplementedError

    def auth_check_is_needed(self, auth_session, response):
        pass

    def phone_number_is_needed(self, auth_session, response):  # noqa: U100
        raise NotImplementedError

    def get_auth_params(self):
        pass

    def authorize(self, auth_session):
        pass

    def _process_auth_url_queries(self, url_queries):
        pass


class DirectUserAPI(UserAPI):
    """Subclass of :class:`vk.session.UserAPI`. Can get access token using user
    credentials (through `Direct authorization <https://dev.vk.ru/api/direct-auth>`__).

    See also:
        `Necessary data <https://gist.github.com/YariKartoshe4ka/02a0f2f49efdac06c423eca5661cfc36>`__
        (**client_id** and **client_secret**) from other official applications

    Args:
        user_login (Optional[str]): User login, optional when using :class:`InteractiveMixin`
        user_password (Optional[str]): User password, optional when using :class:`InteractiveMixin`
        client_id (Optional[int]): ID of the official application, defaults to *"VK for Android"* app ID
        client_secret (Optional[str]): Client secret of the official application, defaults to client
            secret of *"VK for Android"* app
        scope (Optional[Union[str, int]]): Access rights you need. Can be passed
            comma-separated list of scopes, or bitmask sum all of them (see `official
            documentation <https://dev.vk.ru/reference/access-rights>`__). Defaults
            to 'offline'
        **kwargs (any): Additional parameters, which will be passed to each request.
            The most useful is `v` - API version and `lang` - language of responses
            (see :ref:`documentation <Making API request>`)

    Example:
        .. code-block:: python

            >>> import vk
            >>> api = vk.DirectUserAPI(
            ...     user_login='...',
            ...     user_password='...',
            ...     scope='offline,wall',
            ...     v='5.131'
            ... )
            >>> print(api.users.get(user_ids=1))
            [{'id': 1, 'first_name': 'ÐŸÐ°Ð²ÐµÐ»', 'last_name': 'Ð”ÑƒÑ€Ð¾Ð²', ... }]
    """
    LOGIN_URL = 'https://m.vk.ru'
    AUTHORIZE_URL = 'https://oauth.vk.ru/token'

    def __init__(
        self,
        user_login=None,
        user_password=None,
        client_id=2274003,
        client_secret='hHbZxrka2uZ6jB1inYsH',
        scope='offline',
        **kwargs
    ):
        self.user_login = user_login
        self.user_password = user_password
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope

        API.__init__(self, self.get_access_token(), **kwargs)

    def login(self, auth_session):  # noqa: U100
        pass

    def _get_auth_params(self):
        pass

    def authorize(self, auth_session):
        pass

    def auth_check_is_needed(self, auth_session, response_params):
        pass

    def auth_captcha_is_needed(self, auth_session, response_params):
        pass

    def _process_auth_url_queries(self, url_queries):
        pass


class CommunityAPI(UserAPI):
    """Subclass of :class:`vk.session.UserAPI`. Can get community access token using user
    credentials (`Implicit flow authorization for communities
    <https://dev.vk.ru/api/access-token/implicit-flow-community>`__). To select a community
    on behalf of which to make request to the API method, you can pass the **group_id** param
    (defaults to the first community from the passed list)

    Warning:
        This implementation uses the web version of VK to log in and receive cookies, and then
        obtains an access tokens through Implicit flow authorization for communities. In the
        future, VK may change the approach to authorization (for example, replace it with `VK ID
        <https://id.vk.ru>`__) and maintaining operability will become quite a difficult task,
        and most likely it will be **deprecated**.

        You can create a group token on the management page: Community -> Management -> Working with
        API -> Access Tokens -> Create a token (bonus - the token has no expiration date)

    Args:
        user_login (Optional[str]): User login, optional when using :class:`InteractiveMixin`
        user_password (Optional[str]): User password, optional when using :class:`InteractiveMixin`
        group_ids (List[int]): List of community IDs to be authorized
        client_id (Optional[int]): ID of the application to authorize with, defaults to
            "VK Admin" app ID
        scope (Optional[Union[str, int]]): Access rights you need. Can be passed
            comma-separated list of scopes, or bitmask sum all of them (see `official
            documentation <https://dev.vk.ru/reference/access-rights>`__). Defaults
            to ``None``. **Be careful**, only *manage*, *messages*, *photos*, *docs*,
            *wall* and *stories* are available for communities
        **kwargs (any): Additional parameters, which will be passed to each request.
            The most useful is `v` - API version and `lang` - language of responses
            (see :ref:`documentation <Making API request>`)

    Example:
        .. code-block:: python

            >>> import vk
            >>> api = vk.CommunityAPI(
            ...     user_login='...',
            ...     user_password='...',
            ...     group_ids=[123456, 654321],
            ...     scope='messages',
            ...     v='5.131'
            ... )
            >>> print(api.users.get(user_ids=1))
            [{'id': 1, 'first_name': 'ÐŸÐ°Ð²ÐµÐ»', 'last_name': 'Ð”ÑƒÑ€Ð¾Ð²', ... }]
            >>> print(api.users.get(group_id=654321, user_ids=1))
            [{'id': 1, 'first_name': 'ÐŸÐ°Ð²ÐµÐ»', 'last_name': 'Ð”ÑƒÑ€Ð¾Ð²', ... }]
    """

    def __init__(
        self,
        user_login=None,
        user_password=None,
        group_ids=None,
        client_id=6121396,
        scope=None,
        **kwargs
    ):
        self.group_ids = group_ids
        self.default_group_id = None

        self.access_tokens = {}

        super().__init__(user_login, user_password, client_id, scope, **kwargs)

    def get_auth_params(self):
        pass

    def _process_auth_url_queries(self, url_queries):
        pass

    def prepare_request(self, request):
        pass


class InteractiveMixin:
    """Mixin that receives the necessary data from the console

    Example:
        .. code-block:: python

            import vk
            from vk.session import InteractiveMixin

            class API(InteractiveMixin, vk.API):
                pass

            api = API()

            # The input will appear: `VK API access token: `
    """

    def __setattr__(self, name, value):
        attrs = dir(self.__class__)

        if name in attrs and not value:
            return

        if name in filter(lambda x: isinstance(getattr(self.__class__, x), property), attrs):
            return object.__setattr__(self, '_cached_' + name, value)

        return object.__setattr__(self, name, value)

    @property
    def user_login(self):
        pass

    @property
    def user_password(self):
        pass

    @property
    def access_token(self):
        pass

    def get_captcha_key(self, api_error):
        """
        Read CAPTCHA key from shell
        """
        pass

    def get_auth_check_code(self):
        """
        Read Auth code from shell
        """
        pass
