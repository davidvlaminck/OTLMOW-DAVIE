import abc

from requests import Session, Response


class AbstractRequester(Session, metaclass=abc.ABCMeta):
    def __init__(self, first_part_url: str = '', retries: int = 3):
        super().__init__()
        self.first_part_url = first_part_url
        
        if retries < 1:
            raise ValueError("retries must be at least 1")
        self.retries = retries

    @staticmethod
    def _build_failure_message(method: str, retries: int, response: Response, full_url: str) -> str:
        if response is None:
            return f"{method} request failed after {retries} retries. URL: {full_url}. No response received."

        response_url = getattr(response, 'url', full_url)
        body_preview = response.text[:500] if response.text else '<empty>'
        return (
            f"{method} request failed after {retries} retries. "
            f"URL: {response_url}. Status: {response.status_code}. Body: {body_preview}"
        )

    @abc.abstractmethod
    def get(self, url: str = '', **kwargs) -> Response:
        response = None
        full_url = self.first_part_url + url
        for _ in range(self.retries):
            response = super().get(url=full_url, **kwargs)
            if str(response.status_code).startswith('2'):
                return response
        raise RuntimeError(self._build_failure_message('GET', self.retries, response, full_url))

    @abc.abstractmethod
    def post(self, url: str = '', **kwargs) -> Response:
        response = None
        full_url = self.first_part_url + url
        for _ in range(self.retries):
            response = super().post(url=full_url, **kwargs)
            if str(response.status_code).startswith('2'):
                return response
        raise RuntimeError(self._build_failure_message('POST', self.retries, response, full_url))

    @abc.abstractmethod
    def put(self, url: str = '', **kwargs) -> Response:
        response = None
        full_url = self.first_part_url + url
        for _ in range(self.retries):
            response = super().put(url=full_url, **kwargs)
            if str(response.status_code).startswith('2'):
                return response
        raise RuntimeError(self._build_failure_message('PUT', self.retries, response, full_url))

    @abc.abstractmethod
    def patch(self, url: str = '', **kwargs) -> Response:
        response = None
        full_url = self.first_part_url + url
        for _ in range(self.retries):
            response = super().patch(url=full_url, **kwargs)
            if str(response.status_code).startswith('2'):
                return response
        raise RuntimeError(self._build_failure_message('PATCH', self.retries, response, full_url))

    @abc.abstractmethod
    def delete(self, url: str = '', **kwargs) -> Response:
        response = None
        full_url = self.first_part_url + url
        for _ in range(self.retries):
            response = super().delete(url=full_url, **kwargs)
            if str(response.status_code).startswith('2'):
                return response
        raise RuntimeError(self._build_failure_message('DELETE', self.retries, response, full_url))
