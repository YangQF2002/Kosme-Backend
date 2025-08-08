from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


# For our server's response
# Automatically converts to camelCase
class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
    )
