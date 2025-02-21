"""Configuration management for the Nefino MCP server."""

import os
from dataclasses import dataclass


@dataclass
class NefinoConfig:
    """Configuration for the Nefino MCP server."""

    # API credentials
    username: str
    password: str
    jwt_secret: str

    # API endpoint
    base_url: str

    @classmethod
    def from_env(cls) -> "NefinoConfig":
        """Create configuration from environment variables."""
        try:
            return cls(
                username=os.environ["NEFINO_USERNAME"],
                password=os.environ["NEFINO_PASSWORD"],
                jwt_secret=os.environ["NEFINO_JWT_SECRET"],
                base_url=os.environ["NEFINO_BASE_URL"],
            )
        except KeyError as e:
            raise ValueError(f"{e.args[0]} environment variable is required") from e
