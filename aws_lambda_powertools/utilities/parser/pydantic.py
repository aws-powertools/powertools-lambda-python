# Pydantic has many utilities that some advanced customers typically use.
# Importing what's currently in the docs would likely miss something.
# As Pydantic export new types, new utilities, we will have to keep up
# with a project that's not used in our core functionalities.
# For this reason, we're relying on Pydantic's __all__ attr to allow customers
# to use `from aws_lambda_powertools.utilities.parser.pydantic import <anything>`

from pydantic import *  # noqa: F403,F401
