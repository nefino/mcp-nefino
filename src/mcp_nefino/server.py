"""MCP server implementation for Nefino API integration."""

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, List, Optional

from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

from .client import NefinoClient
from .config import NefinoConfig
from .enums import NewsTopic, PlaceTypeNews, RangeOrRecency
from .validation import validate_date_format, validate_date_range, validate_last_n_days


@dataclass
class AppContext:
    """Application context holding configuration and client instances."""
    config: NefinoConfig
    client: NefinoClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Initialize and manage the lifecycle of application dependencies."""
    try:
        config = NefinoConfig.from_env()
        client = NefinoClient(config)
        yield AppContext(config=config, client=client)
    except Exception as e:
        print(f"Failed to initialize Nefino client: {str(e)}")
        raise


mcp = FastMCP("nefino", lifespan=app_lifespan)


@mcp.tool(name="GetNews", description="Useful if you need to retrieve news items for a place")
async def retrieve_news_items_for_place(
    ctx: Context,
    place_id: str = Field(description="The id of the place"),
    place_type: PlaceTypeNews = Field(description="The type of the place (PR, CTY, AU, LAU)"),
    range_or_recency: RangeOrRecency | None = Field(description="Type of search (RANGE or RECENCY)", default=None),
    last_n_days: int | None = Field(description="Number of days to search for (when range_or_recency=RECENCY)", default=None),
    date_range_begin: str | None = Field(description="Start date in YYYY-MM-DD format (when range_or_recency=RANGE)", default=None),
    date_range_end: str | None = Field(description="End date in YYYY-MM-DD format (when range_or_recency=RANGE)", default=None),
    news_topics: List[NewsTopic] | None = Field(description="List of topics to filter by (batteryStorage, gridExpansion, solar, hydrogen, wind)", default=None),
) -> str:
    ctx.session.send_log_message(
        level="info",
        data="Running GetNews tool",
    )
    try:
        # Get client from context
        client = ctx.request_context.lifespan_context.client

        # Validate inputs based on range_or_recency
        if range_or_recency == RangeOrRecency.RECENCY:
            valid, error = validate_last_n_days(last_n_days)
            if not valid:
                return f"Validation error in RangeOrRecency.RECENCY: {error}"

            date_range_begin = None
            date_range_end = None

        elif range_or_recency == RangeOrRecency.RANGE:
            if not validate_date_format(date_range_begin) or not validate_date_format(
                date_range_end
            ):
                return "Validation error: Invalid date format. Use YYYY-MM-DD"

            valid, error = validate_date_range(date_range_begin, date_range_end)
            if not valid:
                return f"Validation error in RangeOrRecency.RANGE: {error}"

            last_n_days = None

        str_place_type = place_type.value
        str_range_or_recency = range_or_recency.value if range_or_recency else None
        str_news_topics = (
            [topic.value for topic in news_topics] if news_topics else None
        )

        result = await client.get_news(
            place_id=place_id,
            place_type=str_place_type,
            range_or_recency=str_range_or_recency,
            last_n_days=last_n_days,
            date_range_begin=date_range_begin,
            date_range_end=date_range_end,
            news_topics=str_news_topics,
        )
        ctx.session.send_log_message(
            level="info",
            data="News items retrieved successfully",
        )   

        return result
    except Exception as e:
        ctx.error(f"Error retrieving news: {str(e)}")
        return f"Failed to retrieve news: {str(e)}"
