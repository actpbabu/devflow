"""Tools for the DevFlow Package Management Agent."""

import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime
from devflow.entities.packages import Package, PackageManagerType, ProgrammingLanguage
from google.adk.tools import BaseTool
from .nuget_api import NuGetAPI
from .google_search import GoogleSearchAPI

logger = logging.getLogger(__name__)

NUGET_API_BASE = "https://api.nuget.org/v3/index.json"

# Initialize API clients
nuget_api = NuGetAPI()
google_search_api = GoogleSearchAPI()

def get_nuget_package_versions(package_id: str) -> Dict:
    """Get all available versions of a NuGet package."""
    return nuget_api.get_package_versions(package_id)

def get_compatible_versions(package_id: str, target_framework: str, 
                          current_version: Optional[str] = None) -> Dict:
    """Get versions compatible with a specific target framework using NuGet API."""
    return nuget_api.get_compatible_versions(package_id, target_framework, current_version)

def get_package_dependencies(package_id: str, version: str, 
                           target_framework: str) -> Dict:
    """Get dependencies for a specific package version."""
    return nuget_api.get_package_dependencies(package_id, version, target_framework)

def check_package_vulnerabilities(package_id: str, version: str) -> Dict:
    """Check for known vulnerabilities in a package version."""
    return nuget_api.check_package_vulnerabilities(package_id, version)

def get_package_metadata(package_id: str, version: str) -> Dict:
    """Get comprehensive metadata for a package version."""
    return nuget_api.get_package_metadata(package_id, version)

def check_package_compatibility_web(package_name: str, current_version: str, 
                                  target_framework: str) -> Dict:
    """Check package compatibility and vulnerabilities using web search.
    
    This tool uses Google Search to find real-world compatibility evidence,
    known vulnerabilities, and recommendations from the community.
    
    Args:
        package_name: Name of the package (e.g., "Newtonsoft.Json")
        current_version: Current version of the package
        target_framework: Target framework (e.g., "net48")
        
    Returns:
        Dict containing compatibility and vulnerability information
    """
    try:
        logger.info(f"Checking web compatibility for {package_name} {current_version} with {target_framework}")
        return google_search_api.check_package_compatibility(
            package_name=package_name,
            current_version=current_version,
            target_framework=target_framework
        )
    except Exception as e:
        logger.error(f"Error in check_package_compatibility_web: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to check compatibility: {str(e)}"
        }

def get_compatible_versions_fallback(
    package_name: str, 
    target_framework: str, 
    current_version: Optional[str] = None
) -> Dict:
    """Get versions compatible with a specific target framework.
    
    Args:
        package_name: Name of the NuGet package
        target_framework: Target .NET framework
        current_version: Current package version (optional)
        
    Returns:
        Dict containing compatible versions
    """
    # If no compatible versions found, use Google Search as fallback
    logger.info(f"No compatible versions found via API for {package_name} with {target_framework}. Trying Google Search...")
    
    # Construct search query
    search_query = f"{package_name} compatible with {target_framework} version compatibility"
    
    try:
        # Perform Google Search
        search_result = google_search_api.search(search_query)
        
        if search_result["status"] == "success":
            # Extract versions from search results
            versions = google_search_api.extract_versions(
                search_result["results"],
                package_name,
                target_framework
            )
            
            if versions:
                return {
                    "status": "success",
                    "package_name": package_name,
                    "target_framework": target_framework,
                    "compatible_versions": versions,
                    "latest_compatible": versions[0],
                    "source": "google_search"
                }
        
        return {
            "status": "error",
            "message": f"No compatible versions found for {package_name} with {target_framework}",
            "source": "google_search"
        }
            
    except Exception as e:
        logger.error(f"Error in Google Search fallback: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to determine compatibility: {str(e)}",
            "source": "google_search"
        }

def check_maven_compatibility(group_id: str, artifact_id: str, 
                            current_version: str, target_runtime: str) -> Dict:
    """Check Maven package compatibility and vulnerabilities using web search.
    
    This tool uses Google Search to find real-world compatibility evidence,
    known vulnerabilities, and recommendations from the community.
    
    Args:
        group_id: Maven group ID (e.g., "org.springframework")
        artifact_id: Maven artifact ID (e.g., "spring-core")
        current_version: Current version of the package
        target_runtime: Target Java runtime (e.g., "java11")
        
    Returns:
        Dict containing compatibility and vulnerability information
    """
    try:
        logger.info(f"Checking Maven compatibility for {group_id}:{artifact_id} {current_version} with {target_runtime}")
        return google_search_api.check_maven_compatibility(
            group_id=group_id,
            artifact_id=artifact_id,
            current_version=current_version,
            target_runtime=target_runtime
        )
    except Exception as e:
        logger.error(f"Error in check_maven_compatibility: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to check compatibility: {str(e)}"
        }

def check_gradle_compatibility(group_id: str, artifact_id: str, 
                             current_version: str, target_runtime: str) -> Dict:
    """Check Gradle package compatibility and vulnerabilities using web search.
    
    This tool uses Google Search to find real-world compatibility evidence,
    known vulnerabilities, and recommendations from the community.
    
    Args:
        group_id: Gradle group ID (e.g., "org.springframework")
        artifact_id: Gradle artifact ID (e.g., "spring-core")
        current_version: Current version of the package
        target_runtime: Target Java runtime (e.g., "java11")
        
    Returns:
        Dict containing compatibility and vulnerability information
    """
    try:
        logger.info(f"Checking Gradle compatibility for {group_id}:{artifact_id} {current_version} with {target_runtime}")
        return google_search_api.check_gradle_compatibility(
            group_id=group_id,
            artifact_id=artifact_id,
            current_version=current_version,
            target_runtime=target_runtime
        )
    except Exception as e:
        logger.error(f"Error in check_gradle_compatibility: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to check compatibility: {str(e)}"
        }
