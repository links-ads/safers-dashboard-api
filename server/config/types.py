from enum import Enum


class EnvironmentTypes(str, Enum):
    """
    The possible types of Environments
    """

    DEVELOPMENT = "development"
    DEPLOYMENT = "deployment"
    CI = "ci"
