from aiohttp import ClientSession


class APIClient:
    def __init__(self, base_url: str):
        self.session = ClientSession()
        self.base_url = base_url

    async def login(self,
                    username: str,
                    password: str) -> str:
        url = f"{self.base_url}/login/token.php"
        data = {
            "username": username,
            "password": password,
            "service": "moodle_mobile_app"
        }
        async with self.session.post(url, data=data) as response:
            json = await response.json()
            return json["token"]

    def with_token(self, token: str):
        return AuthenticatedAPIClient(self.base_url, token)

    async def call_ajax(self, task: str, token: str, **kwargs):
        url = f"{self.base_url}/webservice/rest/server.php"
        data = {
                   "wstoken": token,
                   "wsfunction": task,
                   "moodlewsrestformat": "json",
               } | kwargs

        # Flatten lists to K[IDX] format
        for key in list(data.keys()):
            value = data[key]
            if isinstance(value, list):
                for n, val in enumerate(value):
                    data[f"{key}[{n}]"] = val
                del data[key]

        async with self.session.post(url, data=data) as response:
            return await response.json()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()
        return False


class AuthenticatedAPIClient(APIClient):
    def __init__(self, base_url, token):
        self.token = token
        super().__init__(base_url)

    async def call_ajax(self, task: str, **kwargs):
        return await super().call_ajax(task, self.token, **kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()
        return False
