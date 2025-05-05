# DevFlow Package Management Agent

This project implements an AI-powered package management agent for DevFlow, specializing in NuGet package management and dependency resolution. The agent is designed to help developers find compatible package versions, manage dependencies, and ensure security in their .NET projects.

## Overview

The DevFlow Package Management Agent is designed to provide a comprehensive package management experience for .NET developers. It leverages Gemini to understand package requirements, check compatibility, and provide security recommendations. The agent is designed to be efficient, accurate, and security-focused, ensuring that developers can make informed decisions about their package dependencies.

## Agent Details

The key features of the Package Management Agent include:

| Feature            | Description             |
| ------------------ | ----------------------- |
| _Interaction Type_ | Conversational          |
| _Complexity_       | Advanced               |
| _Agent Type_       | Single Agent           |
| _Components_       | Tools, API Integration |
| _Vertical_         | Development Tools      |

### Agent Architecture

The agent is built using a modular architecture, integrating with the NuGet API and other package management services. It provides tools for version management, dependency resolution, and security analysis. The agent maintains state across interactions to provide consistent recommendations and track package usage.

### Key Features

- **Package Version Management:**
  - Retrieve and analyze available package versions
  - Check compatibility with target frameworks
  - Recommend appropriate versions based on requirements
  - Handle version conflicts and resolution

- **Dependency Management:**
  - Analyze and resolve package dependencies
  - Check for dependency conflicts
  - Provide dependency tree visualization
  - Handle transitive dependencies

- **Security Analysis:**
  - Check for known vulnerabilities
  - Recommend secure versions
  - Provide security best practices
  - Monitor for security updates

- **Framework Compatibility:**
  - Verify framework support
  - Check cross-framework compatibility
  - Handle multi-targeting scenarios
  - Provide migration guidance

#### Tools

The agent has access to the following tools:

- `get_nuget_package_versions(package_name: str) -> Dict`: Retrieves all available versions of a NuGet package.
- `get_compatible_versions(package_name: str, target_framework: str, current_version: Optional[str]) -> Dict`: Gets versions compatible with a specific target framework.
- `get_package_dependencies(package_name: str, version: str, target_framework: str) -> Dict`: Retrieves dependencies for a specific version.
- `check_package_vulnerabilities(package_name: str, version: str) -> Dict`: Checks for known security vulnerabilities.
- `get_package_metadata(package_name: str, version: str) -> Dict`: Retrieves comprehensive package metadata.

## Setup and Installation

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Google ADK SDK (installed via Poetry)
- Google Cloud Project (for Vertex AI Gemini integration)

### Installation

1. **Prerequisites:**

    For the Agent Engine deployment steps, you will need
    a Google Cloud Project. Once you have created your project,
    [install the Google Cloud SDK](https://cloud.google.com/sdk/docs/install).
    Then run the following command to authenticate with your project:
    ```bash
    gcloud auth login
    ```
    You also need to enable certain APIs. Run the following command to enable
    the required APIs:
    ```bash
    gcloud services enable aiplatform.googleapis.com
    ```

2. Clone the repository:
    ```bash
    git clone https://github.com/google/adk-samples.git
    cd adk-samples/agents/devflow
    ```

3. Install dependencies using Poetry:
    ```bash
    poetry install
    poetry env activate
    ```

4. Set up Google Cloud credentials:
    ```bash
    export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_NAME_HERE
    export GOOGLE_GENAI_USE_VERTEXAI=1
    export GOOGLE_CLOUD_LOCATION=us-central1
    ```

## Running the Agent

You can run the agent using the ADK command in your terminal:

1. Run agent in CLI:
    ```bash
    adk run devflow
    ```

2. Run agent with ADK Web UI:
    ```bash
    adk web
    ```
    Select the devflow agent from the dropdown

### Example Interaction

Here's a quick example of how a user might interact with the agent:

**User:**
I need to find a compatible version of Newtonsoft.Json for my .NET 6.0 project.

**Agent:**
I'll help you find a compatible version of Newtonsoft.Json for .NET 6.0. Let me check the available versions and their compatibility.

```tool_code
print(get_compatible_versions("Newtonsoft.Json", "net6.0"))
```

```tool_outputs
{
    "status": "success",
    "package_name": "Newtonsoft.Json",
    "target_framework": "net6.0",
    "compatible_versions": ["13.0.3", "13.0.2", "13.0.1"],
    "latest_compatible": "13.0.3"
}
```

Based on my analysis, version 13.0.3 is the latest version compatible with .NET 6.0. Let me check if there are any known vulnerabilities in this version.

```tool_code
print(check_package_vulnerabilities("Newtonsoft.Json", "13.0.3"))
```

```tool_outputs
{
    "status": "success",
    "package_name": "Newtonsoft.Json",
    "version": "13.0.3",
    "vulnerabilities": [],
    "last_checked": "2024-03-20T10:00:00Z"
}
```

Great news! Version 13.0.3 is secure and compatible with .NET 6.0. Would you like me to show you its dependencies or any other information?

## Configuration

You can find further configuration parameters in [devflow/config.py](./devflow/config.py). This includes parameters such as agent name, app name, and the LLM model used by the agent.

## Deployment on Google Agent Engine

To deploy your agent with all its dependencies:

1. Build the DevFlow Agent WHL file:
    ```bash
    poetry build --format=wheel --output=deployment
    ```

2. Deploy the agent to Agent Engine:
    ```bash
    cd deployment
    python deploy.py
    ```

### Testing Deployment

Here's an example of how to test the deployed agent:

```python
import vertexai
from devflow.config import Config
from vertexai.preview.reasoning_engines import AdkApp

configs = Config()

vertexai.init(
    project="<GOOGLE_CLOUD_LOCATION_PROJECT_ID>",
    location="<GOOGLE_CLOUD_LOCATION>"
)

# Get the agent based on resource id
agent_engine = vertexai.agent_engines.get('DEPLOYMENT_RESOURCE_NAME')

for event in remote_agent.stream_query(
    user_id=USER_ID,
    session_id=session["id"],
    message="What versions of Newtonsoft.Json are compatible with .NET 6.0?",
):
    print(event)
``` 