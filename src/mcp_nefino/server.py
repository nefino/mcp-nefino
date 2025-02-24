"""MCP server implementation for Nefino API integration."""

import json
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

from .client import NefinoClient
from .config import NefinoConfig
from .enums import NewsTopic, PlaceTypeNews, RangeOrRecency
from .validation import validate_date_format, validate_date_range, validate_last_n_days
from .task_manager import TaskManager


@dataclass
class AppContext:
    """Application context holding configuration and client instances."""
    config: NefinoConfig
    client: NefinoClient
    task_manager: TaskManager


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Initialize and manage the lifecycle of application dependencies."""
    try:
        config = NefinoConfig.from_env()
        client = NefinoClient(config)
        task_manager = TaskManager()
        yield AppContext(config=config, client=client, task_manager=task_manager)
    except Exception as e:
        print(f"Failed to initialize Nefino client: {str(e)}")
        raise


mcp = FastMCP("nefino", lifespan=app_lifespan)


@mcp.tool(
    name="StartNewsRetrieval",
    description="Start an asynchronous news retrieval task for a place"
)
async def start_news_retrieval(
    ctx: Context,
    place_id: str = Field(description="The id of the place"),
    place_type: PlaceTypeNews = Field(
        description="The type of the place (PR, CTY, AU, LAU)"
    ),
    range_or_recency: RangeOrRecency | None = Field(
        description="Type of search (RANGE or RECENCY)", default=None
    ),
    last_n_days: int | None = Field(
        description="Number of days to search for (when range_or_recency=RECENCY)",
        default=None,
    ),
    date_range_begin: str | None = Field(
        description="Start date in YYYY-MM-DD format (when range_or_recency=RANGE)",
        default=None,
    ),
    date_range_end: str | None = Field(
        description="End date in YYYY-MM-DD format (when range_or_recency=RANGE)",
        default=None,
    ),
    news_topics: list[NewsTopic] | None = Field(
        description="List of topics to filter by",
        default=None,
    ),
) -> str:
    await ctx.session.send_log_message(
        level="info",
        data="Starting news retrieval task",
    )
    try:
        # Validate inputs based on range_or_recency
        if range_or_recency == RangeOrRecency.RECENCY:
            valid, error = validate_last_n_days(last_n_days)
            if not valid:
                return f"Validation error: {error}"

        elif range_or_recency == RangeOrRecency.RANGE:
            if not validate_date_format(date_range_begin) or not validate_date_format(
                date_range_end
            ):
                return "Validation error: Invalid date format. Use YYYY-MM-DD"

            valid, error = validate_date_range(date_range_begin, date_range_end)
            if not valid:
                return f"Validation error: {error}"

        str_place_type = place_type.value
        str_range_or_recency = range_or_recency.value if range_or_recency else None
        str_news_topics = [topic.value for topic in news_topics] if news_topics else None

        app_ctx = ctx.request_context.lifespan_context
        task_id = app_ctx.task_manager.create_task()

        # Start task execution in background
        asyncio.create_task(
            app_ctx.task_manager.execute_news_task(
                task_id=task_id,
                client=app_ctx.client,
                place_id=place_id,
                place_type=str_place_type,
                range_or_recency=str_range_or_recency,
                last_n_days=last_n_days,
                date_range_begin=date_range_begin,
                date_range_end=date_range_end,
                news_topics=str_news_topics,
            )
        )

        return json.dumps({"task_id": task_id})

    except Exception as e:
        await ctx.session.send_log_message(
            level="error",
            data=f"Error starting news retrieval: {str(e)}",
        )
        return f"Failed to start news retrieval: {str(e)}"

@mcp.tool(
    name="GetNewsResults",
    description="Get the results of a previously started news retrieval task"
)
async def get_news_results(
    ctx: Context,
    task_id: str = Field(description="The task ID returned by StartNewsRetrieval"),
) -> str:
    await ctx.session.send_log_message(
        level="info",
        data=f"Checking news retrieval results for task {task_id}",
    )
    try:
        task = ctx.request_context.lifespan_context.task_manager.get_task(task_id)
        if not task:
            return json.dumps({"error": "Task not found"})

        return json.dumps({
            "status": task.status.value,
            "result": task.result,
            "error": task.error
        }, indent=4, ensure_ascii=False)

    except Exception as e:
        await ctx.session.send_log_message(
            level="error",
            data=f"Error getting news results: {str(e)}",
        )
        return f"Failed to get news results: {str(e)}"
