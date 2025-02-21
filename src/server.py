"""MCP server implementation for Nefino API integration."""

from contextlib import asynccontextmanager
from typing import AsyncIterator, List, Optional

from mcp.server.fastmcp import Context, FastMCP

from .client import NefinoClient
from .config import NefinoConfig
from .validation import validate_date_format, validate_date_range, validate_last_n_days


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Manage server startup and shutdown lifecycle."""
    try:
        # Initialize Nefino client on startup
        config = NefinoConfig.from_env()
        client = NefinoClient(config)
        server.info(f"Nefino client initialized with base URL: {config.base_url}")
        yield {"client": client}
    except Exception as e:
        server.error(f"Failed to initialize Nefino client: {str(e)}")
        raise


# Create the MCP server
mcp = FastMCP(
    "nefino",
    lifespan=server_lifespan,
)


@mcp.tool()
async def retrieve_news_items_for_place(
    ctx: Context,
    place_id: str,
    place_type: PlaceTypeNews,
    range_or_recency: Optional[RangeOrRecency] = None,
    last_n_days: Optional[int] = None,
    date_range_begin: Optional[str] = None,
    date_range_end: Optional[str] = None,
    news_topics: Optional[List[NewsTopic]] = None,
) -> str:
    """Fetch news items for a place.

    Args:
        place_id: The id of the place
        place_type: The type of the place (PR, CTY, AU, LAU)
        range_or_recency: Type of search (RANGE or RECENCY)
        last_n_days: Number of days to search for (when range_or_recency=RECENCY)
        date_range_begin: Start date in YYYY-MM-DD format (when range_or_recency=RANGE)
        date_range_end: End date in YYYY-MM-DD format (when range_or_recency=RANGE)
        news_topics: List of topics to filter by (batteryStorage, gridExpansion, solar, hydrogen, wind)

    Returns:
        JSON string containing the news items
    """
    try:
        # Validate inputs based on range_or_recency
        if range_or_recency == RangeOrRecency.RECENCY:
            valid, error = validate_last_n_days(last_n_days)
            if not valid:
                return f"Validation error in RangeOrRecency.RECENCY: {error}"

            # Clear date range parameters when using recency
            date_range_begin = None
            date_range_end = None

        elif range_or_recency == RangeOrRecency.RANGE:
            # Validate date formats
            if not validate_date_format(date_range_begin) or not validate_date_format(
                date_range_end
            ):
                return "Validation error: Invalid date format. Use YYYY-MM-DD"

            # Validate date range
            valid, error = validate_date_range(date_range_begin, date_range_end)
            if not valid:
                return f"Validation error in RangeOrRecency.RANGE: {error}"

            # Clear last_n_days when using range
            last_n_days = None

        client = ctx.request_context.lifespan_context["client"]

        # Convert enums to strings for the API
        str_place_type = place_type.value
        str_range_or_recency = range_or_recency.value if range_or_recency else None
        str_news_topics = (
            [topic.value for topic in news_topics] if news_topics else None
        )

        # Make the API call
        result = client.get_news(
            place_id=place_id,
            place_type=str_place_type,
            range_or_recency=str_range_or_recency,
            last_n_days=last_n_days,
            date_range_begin=date_range_begin,
            date_range_end=date_range_end,
            news_topics=str_news_topics,
        )

        return result
    except Exception as e:
        ctx.error(f"Error retrieving news: {str(e)}")
        return f"Failed to retrieve news: {str(e)}"


if __name__ == "__main__":
    mcp.run()
