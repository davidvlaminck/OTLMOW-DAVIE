import datetime
import json
import string
import sys
from pathlib import Path
from random import choice

import aiohttp
import jwt
from aiohttp import ClientSession, ClientResponse
from jwt import algorithms as jwt_algo


class JWTAsyncRequester:
    def __init__(self, private_key_path: Path, client_id: str, first_part_url: str = ''):
        if 'cryptography' not in sys.modules:
            raise ModuleNotFoundError('needs module cryptography to work')

        self.private_key_path: Path = private_key_path
        self.client_id: str = client_id
        self.first_part_url: str = first_part_url

        self.oauth_token: str = ''
        self.expires: datetime.datetime = datetime.datetime.utcnow() - datetime.timedelta(seconds=1)
        self.requested_at: datetime.datetime = self.expires

        self._session = ClientSession()

    async def get(self, url='', **kwargs) -> ClientResponse:
        kwargs = await self.modify_kwargs_for_bearer_token(kwargs)
        return await self._session.get(url=self.first_part_url + url, **kwargs)

    async def post(self, url='', **kwargs) -> (ClientResponse, dict):
        kwargs = await self.modify_kwargs_for_bearer_token(kwargs)
        return await self._session.post(url=self.first_part_url + url, **kwargs)

    async def get_oauth_token(self) -> str:
        if self.expires > datetime.datetime.utcnow():
            return self.oauth_token

        authentication_token = self.generate_authentication_token()
        self.oauth_token, expires_in = await self.get_access_token(authentication_token)
        self.expires = self.requested_at + datetime.timedelta(seconds=expires_in) - datetime.timedelta(minutes=1)

        return self.oauth_token

    async def modify_kwargs_for_bearer_token(self, kwargs: dict) -> dict:
        bearer_token = await self.get_oauth_token()
        if 'headers' not in kwargs:
            kwargs['headers'] = {}

        for arg in kwargs:
            if arg == 'headers':
                headers = kwargs[arg]
                if 'accept' not in headers:
                    headers['accept'] = ''
                if headers['accept'] is not None:
                    if headers['accept'] != '':
                        headers['accept'] = f"{headers['accept']}, application/json"
                    else:
                        headers['accept'] = 'application/json'
                headers['authorization'] = f'Bearer {bearer_token}'
                if 'Content-Type' not in headers or headers['Content-Type'] is None:
                    headers['Content-Type'] = 'application/vnd.awv.eminfra.v1+json'
                kwargs['headers'] = headers

        return kwargs

    def generate_authentication_token(self) -> str:
        self.requested_at = datetime.datetime.utcnow()
        # Authentication token generation
        payload = {'iss': self.client_id,
                   'sub': self.client_id,
                   'aud': 'https://authenticatie.vlaanderen.be/op',
                   'exp': self.requested_at + datetime.timedelta(minutes=9),
                   'jti': ''.join(choice(string.ascii_lowercase) for _ in range(20))
                   }

        with open(self.private_key_path) as private_key:
            private_key_json = json.load(private_key)
            key = jwt_algo.RSAAlgorithm.from_jwk(private_key_json)
            token = jwt.encode(payload=payload, key=key, algorithm='RS256')

        return token

    async def get_access_token(self, token: str) -> (str, int):
        # Authorization access token generation
        url = 'https://authenticatie.vlaanderen.be/op/v1/token'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        request_body = {
            'grant_type': 'client_credentials',
            'scope': 'awv_toep_services',
            'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
            'client_id': self.client_id,
            "client_assertion": token
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=request_body, headers=headers) as response:
                # Check for HTTP codes other than 200
                if response.status != 200:
                    print('Status:', response.status, 'Headers:', response.headers, 'Error Response:', response.content)
                    raise RuntimeError(f'Could not get the acces token: {response.content}')

                response_json = await response.json()

                return response_json['access_token'], response_json['expires_in']
