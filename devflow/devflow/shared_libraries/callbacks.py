"""Callback functions for DevFlow Package Management Agent."""

import logging
import time
from typing import Any, Dict
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest
from google.adk.tools import BaseTool
from google.adk.agents.invocation_context import InvocationContext
from ..entities.packages import Package, PackageManagerType

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

RATE_LIMIT_SECS = 60
RPM_QUOTA = 10


def rate_limit_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> None:
    """Callback function that implements a query rate limit.

    Args:
      callback_context: A CallbackContext obj representing the active callback
        context.
      llm_request: A LlmRequest obj representing the active LLM request.
    """
    for content in llm_request.contents:
        for part in content.parts:
            if part.text == "":
                part.text = " "

    now = time.time()
    if "timer_start" not in callback_context.state:
        callback_context.state["timer_start"] = now
        callback_context.state["request_count"] = 1
        logger.debug(
            "rate_limit_callback [timestamp: %i, req_count: 1, elapsed_secs: 0]",
            now,
        )
        return

    request_count = callback_context.state["request_count"] + 1
    elapsed_secs = now - callback_context.state["timer_start"]
    logger.debug(
        "rate_limit_callback [timestamp: %i, request_count: %i, elapsed_secs: %i]",
        now,
        request_count,
        elapsed_secs,
    )

    if request_count > RPM_QUOTA:
        delay = RATE_LIMIT_SECS - elapsed_secs + 1
        if delay > 0:
            logger.debug("Sleeping for %i seconds", delay)
            time.sleep(delay)
        callback_context.state["timer_start"] = now
        callback_context.state["request_count"] = 1
    else:
        callback_context.state["request_count"] = request_count

    return


def lowercase_value(value):
    """Make dictionary values lowercase for consistency in package names and versions."""
    if isinstance(value, dict):
        return {k: lowercase_value(v) for k, v in value.items()}
    elif isinstance(value, str):
        return value.lower()
    elif isinstance(value, (list, set, tuple)):
        tp = type(value)
        return tp(lowercase_value(i) for i in value)
    else:
        return value


def before_tool(
    tool: BaseTool, args: Dict[str, Any], tool_context: CallbackContext
) -> Dict[str, Any]:
    """Pre-process tool calls for package management operations.

    Args:
        tool: The tool being called
        args: Arguments passed to the tool
        tool_context: Context for the tool call

    Returns:
        Optional result to override tool execution
    """
    # Ensure consistent casing for package names and versions
    args = lowercase_value(args)

    # Package installation validation
    if tool.name == "install_package":
        package_name = args.get("package_name", "")
        version = args.get("version", "")
        if not package_name or not version:
            return {"result": "Package name and version are required for installation."}
        
        # Check for known vulnerable versions
        if "vulnerable_version" in args.get("version", ""):
            return {"result": "This version has known security vulnerabilities. Please use a different version."}

    # Dependency resolution
    if tool.name == "resolve_dependencies":
        package_manager = args.get("package_manager", "")
        if package_manager not in [pm.value for pm in PackageManagerType]:
            return {"result": f"Unsupported package manager: {package_manager}"}

    # Package update validation
    if tool.name == "update_package":
        current_version = args.get("current_version", "")
        target_version = args.get("target_version", "")
        if not current_version or not target_version:
            return {"result": "Both current and target versions are required for update."}

    return None


def before_agent(callback_context: InvocationContext):
    """Initialize package management state before agent execution.

    Args:
        callback_context: Context for the agent invocation
    """
    if "package_state" not in callback_context.state:
        # Initialize with a default package state
        callback_context.state["package_state"] = {
            "active_package": None,
            "package_manager": PackageManagerType.PIP.value,
            "dependencies": {},
            "vulnerabilities": [],
            "last_updated": time.time()
        }

    # Load default package if needed
    if "active_package" not in callback_context.state["package_state"]:
        default_package = Package.get_package("devflow-core", PackageManagerType.PIP)
        if default_package:
            callback_context.state["package_state"]["active_package"] = default_package.to_json()
