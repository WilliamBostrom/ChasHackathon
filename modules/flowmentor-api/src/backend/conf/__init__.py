from pydantic import BaseModel

from ..utils import auth, env, log
from ..utils.env import EnvVarSpec
from . import temporal

logger = log.get_logger(__name__)

# Set to True to enable authentication
USE_AUTH = False

# Set to True to enable Twilio SMS functionality
USE_TWILIO = False

# Set to True to enable database
USE_DATABASE = True

#### Types ####


class HttpServerConf(BaseModel):
    host: str
    port: int
    autoreload: bool


#### Env Vars ####

## Auth ##

AUTH_OIDC_JWK_URL = EnvVarSpec(id="AUTH_OIDC_JWK_URL", is_optional=True)
AUTH_OIDC_AUDIENCE = EnvVarSpec(id="AUTH_OIDC_AUDIENCE", is_optional=True)
AUTH_OIDC_ISSUER = EnvVarSpec(id="AUTH_OIDC_ISSUER", is_optional=True)

## Logging ##

LOG_LEVEL = EnvVarSpec(id="LOG_LEVEL", default="INFO")

## HTTP ##

HTTP_HOST = EnvVarSpec(id="HTTP_HOST", default="0.0.0.0")

HTTP_PORT = EnvVarSpec(id="HTTP_PORT", default="8000")

HTTP_AUTORELOAD = EnvVarSpec(
    id="HTTP_AUTORELOAD",
    parse=lambda x: x.lower() == "true",
    default="false",
    type=(bool, ...),
)

HTTP_EXPOSE_ERRORS = EnvVarSpec(
    id="HTTP_EXPOSE_ERRORS",
    default="false",
    parse=lambda x: x.lower() == "true",
    type=(bool, ...),
)

## Twilio ##

TWILIO_ACCOUNT_SID = EnvVarSpec(id="TWILIO_ACCOUNT_SID", is_optional=True)

TWILIO_AUTH_TOKEN = EnvVarSpec(id="TWILIO_AUTH_TOKEN", is_optional=True, is_secret=True)

TWILIO_FROM_PHONE_NUMBER = EnvVarSpec(id="TWILIO_FROM_PHONE_NUMBER", is_optional=True)

## PostgreSQL Database ##

DATABASE_HOST = EnvVarSpec(id="DATABASE_HOST", default="localhost")

DATABASE_PORT = EnvVarSpec(id="DATABASE_PORT", default="5432")

DATABASE_NAME = EnvVarSpec(id="DATABASE_NAME", default="flowmentor")

DATABASE_USERNAME = EnvVarSpec(id="DATABASE_USERNAME", default="postgres")

DATABASE_PASSWORD = EnvVarSpec(
    id="DATABASE_PASSWORD", default="password", is_secret=True
)

#### Validation ####
VALIDATED_ENV_VARS = [
    HTTP_AUTORELOAD,
    HTTP_EXPOSE_ERRORS,
    HTTP_PORT,
    LOG_LEVEL,
]

VALIDATED_ENV_VARS.extend(temporal.VALIDATED_ENV_VARS)


# Only validate auth vars if USE_AUTH is True
if USE_AUTH:
    VALIDATED_ENV_VARS.extend(
        [
            AUTH_OIDC_JWK_URL,
            AUTH_OIDC_AUDIENCE,
            AUTH_OIDC_ISSUER,
        ]
    )

# Only validate Twilio vars if USE_TWILIO is True
if USE_TWILIO:
    VALIDATED_ENV_VARS.extend(
        [
            TWILIO_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN,
            TWILIO_FROM_PHONE_NUMBER,
        ]
    )

# Only validate database vars if USE_DATABASE is True
if USE_DATABASE:
    VALIDATED_ENV_VARS.extend(
        [
            DATABASE_HOST,
            DATABASE_PORT,
            DATABASE_NAME,
            DATABASE_USERNAME,
            DATABASE_PASSWORD,
        ]
    )


def validate() -> bool:
    return env.validate(VALIDATED_ENV_VARS)


#### Getters ####


def get_auth_config() -> auth.AuthClientConfig:
    """Get authentication configuration."""
    return auth.AuthClientConfig(
        jwk_url=env.parse(AUTH_OIDC_JWK_URL),
        audience=env.parse(AUTH_OIDC_AUDIENCE),
        issuer=env.parse(AUTH_OIDC_ISSUER),
    )


def get_http_expose_errors() -> str:
    return env.parse(HTTP_EXPOSE_ERRORS)


def get_log_level() -> str:
    return env.parse(LOG_LEVEL)


def get_http_conf() -> HttpServerConf:
    return HttpServerConf(
        host=env.parse(HTTP_HOST),
        port=env.parse(HTTP_PORT),
        autoreload=env.parse(HTTP_AUTORELOAD),
    )


def get_twilio_conf():
    """Get Twilio configuration."""
    # Import here to avoid circular dependency
    from ..clients.twilio import TwilioConf

    return TwilioConf(
        account_sid=env.parse(TWILIO_ACCOUNT_SID),
        auth_token=env.parse(TWILIO_AUTH_TOKEN),
        from_phone_number=env.parse(TWILIO_FROM_PHONE_NUMBER),
    )


def get_database_conf():
    """Get PostgreSQL database configuration."""
    # Import here to avoid circular dependency
    from ..clients.database import DatabaseConf

    return DatabaseConf(
        host=env.parse(DATABASE_HOST),
        port=int(env.parse(DATABASE_PORT)),
        database=env.parse(DATABASE_NAME),
        username=env.parse(DATABASE_USERNAME),
        password=env.parse(DATABASE_PASSWORD),
    )
