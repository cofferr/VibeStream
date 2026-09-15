from config import settings
from vibestream_common.auth_middleware import AuthMiddleware as _BaseAuthMiddleware


class AuthMiddleware(_BaseAuthMiddleware):
    def __init__(self, app):
        super().__init__(
            app,
            jwt_secret=settings.jwt_secret,
            jwt_algorithm=settings.jwt_algorithm,
            public_path_prefixes=("/health", "/files"),
        )
