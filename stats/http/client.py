"""HTTP Client."""

# Standard Library
import re
import json as _json
import socket
import asyncio
import logging

# Third Party
import httpx

# Project
from stats.util import make_repr, split_on_uppercase

DEFAULT_LOGGER = logging.getLogger(__file__)


class BaseHttpClient:
    """Base session handler."""

    def __init__(
        self,
        base_url,
        config=None,
        uri_prefix="",
        uri_suffix="",
        verify_ssl=True,
        timeout=10,
        logger=DEFAULT_LOGGER,
        exception_class=Exception,
        user_agent=f"httpx/{httpx.__version__}",
    ):
        """Initialize connection instance."""
        self.__name__ = self.name
        self.config = config
        self.protocol, self.host, self.port = self._parse_url_string(base_url)
        self.base_url = self._build_url_string(self.protocol, self.host, self.port)
        self.uri_prefix = uri_prefix.strip("/")
        self.uri_suffix = uri_suffix.strip("/")
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.log = logger
        self.exception_class = exception_class
        self.user_agent = user_agent

        session_args = {
            "verify": self.verify_ssl,
            "base_url": self.base_url,
            "timeout": self.timeout,
        }
        self._session = httpx.Client(**session_args)
        self._asession = httpx.AsyncClient(**session_args)

    @classmethod
    def __init_subclass__(cls, name=None, **kwargs):
        """Set correct subclass name."""
        super().__init_subclass__(**kwargs)
        cls.name = name or cls.__name__

    async def __aenter__(self):
        """Test connection on entry."""
        available = await self._atest()

        if available:
            self.log.debug("Initialized session with {}", self.base_url)
            return self
        else:
            raise self._exception(f"Unable to create session to {self.name}")

    async def __aexit__(self, exc_type=None, exc_value=None, traceback=None):
        """Close connection on exit."""
        self.log.debug("Closing session with {}", self.base_url)

        await self._asession.aclose()

    def __enter__(self):
        """Test connection on entry."""
        available = self._test()

        if available:
            self.log.debug("Initialized session with {}", self.base_url)
            return self
        else:
            raise self._exception(f"Unable to create session to {self.name}")

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        """Close connection on exit."""
        if exc_type is not None:
            self.log.error(traceback)
        self._session.close()

    def __repr__(self):
        """Return user friendly representation of instance."""
        return make_repr(self)

    def _exception(self, message, exc=None, **kwargs):
        """Add stringified exception to message if passed."""
        if exc is not None:
            message = "{}: {}".format(str(message), str(exc), **kwargs)

        return self.exception_class(message)

    def _test(self):
        """Open a low-level connection to the base URL to ensure its port is open."""
        self.log.debug("Testing connection to {}", self.base_url)

        try:
            test_host = re.sub(r"http(s)?\:\/\/", "", self.base_url)
            socket.socket().connect((test_host, 443))

        except socket.gaierror as err:
            raise self._exception(
                f"{self.name} appears to be unreachable", err
            ) from None

        return True

    async def _atest(self):
        """Open a low-level connection to the base URL to ensure its port is open."""
        self.log.debug("Testing connection to {}", self.base_url)

        try:
            _reader, _writer = await asyncio.open_connection(self.host, self.port)

        except socket.gaierror as err:
            raise self._exception(
                f"{self.name} appears to be unreachable at {self.base_url}", err
            )

        if _reader or _writer:
            return True
        else:
            return False

    @staticmethod
    def _build_url_string(protocol, host, port):
        port = str(port)
        if port == "80":
            port = ""
            protocol = "http"
        elif port == "443":
            port = ""
            protocol = "https"

        if port != "":
            port = f":{port}"
        return "{protocol}://{host}{port}".format(
            protocol=protocol, host=host, port=port
        )

    @staticmethod
    def _parse_url_string(url):
        [url_parts] = re.findall(r"^(http[s]?):\/\/([^:]+)\:?(\d*)$", url)
        protocol, host, port = url_parts

        return protocol, host, int(port)

    @staticmethod
    def _prepare_dict(_dict):
        return _json.loads(_json.dumps(_dict, default=str))

    def _parse_response(self, response):
        parsed = {}
        try:
            parsed = response.json()
        except _json.JSONDecodeError:
            try:
                parsed = _json.loads(response)
            except (_json.JSONDecodeError, TypeError):
                self.log.error("Error parsing JSON for response {}", repr(response))
                parsed = {"data": response.text}
        return parsed

    @staticmethod
    def _parse_exception(exc):
        """Parse an exception and its direct cause."""

        if not isinstance(exc, BaseException):
            raise TypeError(f"'{repr(exc)}' is not an exception.")

        def get_exc_name(exc):
            return " ".join(split_on_uppercase(exc.__class__.__name__))

        def get_doc_summary(doc):
            return doc.strip().split("\n")[0].strip(".")

        name = get_exc_name(exc)
        parsed = []
        if exc.__doc__:
            detail = get_doc_summary(exc.__doc__)
            parsed.append(f"{name} ({detail})")
        else:
            parsed.append(name)

        if exc.__cause__:
            cause = get_exc_name(exc.__cause__)
            if exc.__cause__.__doc__:
                cause_detail = get_doc_summary(exc.__cause__.__doc__)
                parsed.append(f"{cause} ({cause_detail})")
            else:
                parsed.append(cause)
        return ", caused by ".join(parsed)

    def _build_request(self, **kwargs):
        """Process requests parameters into structure usable by http library."""
        from operator import itemgetter

        supported_methods = ("GET", "POST", "PUT", "DELETE", "HEAD", "PATCH")

        (
            method,
            endpoint,
            item,
            headers,
            params,
            data,
            timeout,
            response_required,
        ) = itemgetter(*kwargs.keys())(kwargs)

        if method.upper() not in supported_methods:
            raise self._exception(
                f'Method must be one of {", ".join(supported_methods)}. '
                f"Got: {str(method)}"
            )

        endpoint = "/".join(
            i
            for i in (
                "",
                self.uri_prefix.strip("/"),
                endpoint.strip("/"),
                self.uri_suffix.strip("/"),
                item,
            )
            if i
        )

        request = {
            "method": method,
            "url": endpoint,
            "headers": {"user-agent": self.user_agent},
        }

        if headers is not None:
            request.update({"headers": headers})

        if params is not None:
            params = {str(k): str(v) for k, v in params.items() if v is not None}
            request["params"] = params

        if data is not None:
            if not isinstance(data, dict):
                raise self._exception(f"Data must be a dict, got: {str(data)}")
            request["json"] = self._prepare_dict(data)

        if timeout is not None:
            if not isinstance(timeout, int):
                try:
                    timeout = int(timeout)
                except TypeError:
                    raise self._exception(
                        f"Timeout must be an int, got: {str(timeout)}"
                    )
            request["timeout"] = timeout

        self.log.debug("Constructed request parameters {}", request)
        return request

    async def _arequest(  # noqa: C901
        self,
        method,
        endpoint,
        item=None,
        headers=None,
        params=None,
        data=None,
        timeout=None,
        response_required=False,
    ):
        """Run HTTP POST operation."""
        request = self._build_request(
            method=method,
            endpoint=endpoint,
            item=item,
            headers=None,
            params=params,
            data=data,
            timeout=timeout,
            response_required=response_required,
        )

        try:
            response = await self._asession.request(**request)

            if response.status_code not in range(200, 300):
                status = httpx.StatusCode(response.status_code)
                error = self._parse_response(response)
                raise self._exception(
                    f'{status.name.replace("_", " ")}: {error}', level="danger"
                ) from None

        except httpx.HTTPError as http_err:
            raise self._exception(self._parse_exception(http_err)) from None

        return self._parse_response(response)

    async def _aget(self, endpoint, **kwargs):
        return await self._arequest(method="GET", endpoint=endpoint, **kwargs)

    async def _apost(self, endpoint, **kwargs):
        return await self._arequest(method="POST", endpoint=endpoint, **kwargs)

    async def _aput(self, endpoint, **kwargs):
        return await self._arequest(method="PUT", endpoint=endpoint, **kwargs)

    async def _adelete(self, endpoint, **kwargs):
        return await self._arequest(method="DELETE", endpoint=endpoint, **kwargs)

    async def _apatch(self, endpoint, **kwargs):
        return await self._arequest(method="PATCH", endpoint=endpoint, **kwargs)

    async def _ahead(self, endpoint, **kwargs):
        return await self._arequest(method="HEAD", endpoint=endpoint, **kwargs)

    def _request(  # noqa: C901
        self,
        method,
        endpoint,
        item=None,
        headers=None,
        params=None,
        data=None,
        timeout=None,
        response_required=False,
    ):
        """Run HTTP POST operation."""
        request = self._build_request(
            method=method,
            endpoint=endpoint,
            item=item,
            headers=None,
            params=params,
            data=data,
            timeout=timeout,
            response_required=response_required,
        )

        try:
            response = self._session.request(**request)

            if response.status_code not in range(200, 300):
                status = httpx.StatusCode(response.status_code)
                error = self._parse_response(response)
                raise self._exception(
                    f'{status.name.replace("_", " ")}: {error}', level="danger"
                ) from None

        except httpx.HTTPError as http_err:
            raise self._exception(
                self._parse_exception(http_err), level="danger"
            ) from None

        return self._parse_response(response)

    def _get(self, endpoint, **kwargs):
        return self._request(method="GET", endpoint=endpoint, **kwargs)

    def _post(self, endpoint, **kwargs):
        return self._request(method="POST", endpoint=endpoint, **kwargs)

    def _put(self, endpoint, **kwargs):
        return self._request(method="PUT", endpoint=endpoint, **kwargs)

    def _delete(self, endpoint, **kwargs):
        return self._request(method="DELETE", endpoint=endpoint, **kwargs)

    def _patch(self, endpoint, **kwargs):
        return self._request(method="PATCH", endpoint=endpoint, **kwargs)

    def _head(self, endpoint, **kwargs):
        return self._request(method="HEAD", endpoint=endpoint, **kwargs)
