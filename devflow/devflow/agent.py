"""Agent module for the DevFlow Package Management Agent."""

import logging
import warnings
from google.adk import Agent
from .config import Config
from .prompts import GLOBAL_INSTRUCTION, INSTRUCTION
from .shared_libraries.callbacks import (
    rate_limit_callback,
    before_agent,
    before_tool,
)
from .tools.tools import (
    get_nuget_package_versions,
    get_compatible_versions,
    get_package_dependencies,
    check_package_vulnerabilities,
    get_package_metadata,
    check_package_compatibility_web,
    check_maven_compatibility,
    check_gradle_compatibility,
)

warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")

configs = Config()

# configure logging __name__
logger = logging.getLogger(__name__)

root_agent = Agent(
    model=configs.agent_settings.model,
    global_instruction=GLOBAL_INSTRUCTION,
    instruction=INSTRUCTION,
    name=configs.agent_settings.name,
    tools=[
        get_nuget_package_versions,
        get_compatible_versions,
        get_package_dependencies,
        check_package_vulnerabilities,
        get_package_metadata,
        check_package_compatibility_web,
        check_maven_compatibility,
        check_gradle_compatibility,
    ],
    before_tool_callback=before_tool,
    before_agent_callback=before_agent,
    before_model_callback=rate_limit_callback,
)
