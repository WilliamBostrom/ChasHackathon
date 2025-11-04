from pydantic import BaseModel

from ..utils import auth, env, log
from ..utils.env import EnvVarSpec
from . import temporal

logger = log.get_logger(__name__)

# Set to True to enable authentication
USE_AUTH = False

# Set to True to enable Twilio SMS functionality
USE_TWILIO = False

# Set to True to enable Couchbase
USE_COUCHBASE = True

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

## Couchbase ##

COUCHBASE_CONNECTION_STRING = EnvVarSpec(
    id="COUCHBASE_CONNECTION_STRING", default="couchbase://couchbase"
)

COUCHBASE_USERNAME = EnvVarSpec(id="COUCHBASE_USERNAME", default="Administrator")

COUCHBASE_PASSWORD = EnvVarSpec(
    id="COUCHBASE_PASSWORD", default="password", is_secret=True
)

COUCHBASE_BUCKET = EnvVarSpec(id="COUCHBASE_BUCKET", default="flowmentor")

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

# Only validate Couchbase vars if USE_COUCHBASE is True
if USE_COUCHBASE:
    VALIDATED_ENV_VARS.extend(
        [
            COUCHBASE_CONNECTION_STRING,
            COUCHBASE_USERNAME,
            COUCHBASE_PASSWORD,
            COUCHBASE_BUCKET,
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


def get_couchbase_conf():
    """Get Couchbase configuration."""
    # Import here to avoid circular dependency
    from ..clients.couchbase import CouchbaseConf

    return CouchbaseConf(
        connection_string=env.parse(COUCHBASE_CONNECTION_STRING),
        username=env.parse(COUCHBASE_USERNAME),
        password=env.parse(COUCHBASE_PASSWORD),
        bucket_name=env.parse(COUCHBASE_BUCKET),
    )
