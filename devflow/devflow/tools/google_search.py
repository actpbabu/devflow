"""Google Custom Search API integration for package compatibility checking."""

import logging
import os
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from ..config import Config

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class GoogleSearchAPI:
    """Client for interacting with Google Custom Search API."""
    
    # Java runtime compatibility mapping
    JAVA_RUNTIME_COMPATIBILITY = {
        "java21": ["java20", "java19", "java18", "java17", "java16", "java15", "java14", "java13", "java12", "java11", "java8"],
        "java20": ["java19", "java18", "java17", "java16", "java15", "java14", "java13", "java12", "java11", "java8"],
        "java19": ["java18", "java17", "java16", "java15", "java14", "java13", "java12", "java11", "java8"],
        "java18": ["java17", "java16", "java15", "java14", "java13", "java12", "java11", "java8"],
        "java17": ["java16", "java15", "java14", "java13", "java12", "java11", "java8"],
        "java16": ["java15", "java14", "java13", "java12", "java11", "java8"],
        "java15": ["java14", "java13", "java12", "java11", "java8"],
        "java14": ["java13", "java12", "java11", "java8"],
        "java13": ["java12", "java11", "java8"],
        "java12": ["java11", "java8"],
        "java11": ["java8"],
        "java8": ["java8"]
    }

    def __init__(self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None):
        """Initialize the Google Search API client.
        
        Args:
            api_key: Google Custom Search API key
            search_engine_id: Custom Search Engine ID
        """
        # Get config instance
        config = Config()
        
        # Try to get credentials from parameters first, then config, then environment variables
        self.api_key = api_key or config.SEARCH_API_KEY or os.getenv("GOOGLE_SEARCH_API_KEY")
        self.search_engine_id = search_engine_id or config.SEARCH_ENGINE_ID or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        # Log the state of credentials (without exposing actual values)
        logger.debug("Checking Google Search API credentials...")
        logger.debug(f"API Key present: {'Yes' if self.api_key else 'No'}")
        logger.debug(f"Search Engine ID present: {'Yes' if self.search_engine_id else 'No'}")
        
        if not self.api_key or not self.search_engine_id:
            error_msg = (
                "Google Search API credentials not found. "
                "Please ensure you have a .env file in your project root with:\n"
                "GOOGLE_SEARCH_API_KEY=your_api_key\n"
                "GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id\n\n"
                "Current working directory: " + os.getcwd()
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            self.service = build("customsearch", "v1", developerKey=self.api_key)
            logger.info("Google Search API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Search API client: {str(e)}")
            raise
    
    def search(self, query: str, num_results: int = 5) -> Dict:
        """Perform a search using Google Custom Search API.
        
        Args:
            query: Search query
            num_results: Number of results to return (max 10)
            
        Returns:
            Dict containing search results
        """
        try:
            # Ensure num_results is within allowed range
            num_results = min(max(1, num_results), 10)
            
            # Perform the search
            result = self.service.cse().list(
                q=query,
                cx=self.search_engine_id,
                num=num_results
            ).execute()
            
            # Extract relevant information from results
            items = result.get("items", [])
            search_results = []
            
            for item in items:
                search_results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "pagemap": item.get("pagemap", {})
                })
            
            return {
                "status": "success",
                "total_results": result.get("searchInformation", {}).get("totalResults", 0),
                "results": search_results
            }
            
        except HttpError as e:
            logger.error(f"Google Search API error: {str(e)}")
            return {
                "status": "error",
                "message": f"Google Search API error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}")
            return {
                "status": "error",
                "message": f"Error performing search: {str(e)}"
            }
    
    def extract_versions(self, search_results: List[Dict], package_name: str, 
                        target_framework: str) -> List[str]:
        """Extract version numbers from search results.
        
        Args:
            search_results: List of search results
            package_name: Name of the package
            target_framework: Target framework
            
        Returns:
            List of extracted version numbers
        """
        versions = set()
        
        for result in search_results:
            # Combine title and snippet for better context
            text = f"{result['title']} {result['snippet']}".lower()
            
            # Only process results that mention both package and framework
            if (package_name.lower() in text and 
                target_framework.lower() in text):
                
                # Look for version numbers in the format x.y.z
                version_matches = re.findall(r'\d+\.\d+\.\d+', text)
                versions.update(version_matches)
                
                # Also look for version numbers in the format x.y
                version_matches = re.findall(r'\d+\.\d+(?!\.)', text)
                versions.update(version_matches)
        
        return sorted(list(versions), reverse=True)

    def check_package_compatibility(self, package_name: str, current_version: str, 
                                  target_framework: str) -> Dict:
        """Check package compatibility and vulnerabilities using Google Search.
        
        Args:
            package_name: Name of the package (e.g., "Newtonsoft.Json")
            current_version: Current version of the package
            target_framework: Target framework (e.g., "net48")
            
        Returns:
            Dict containing compatibility and vulnerability information
        """
        try:
            logger.info(f"Checking compatibility for {package_name} {current_version} with {target_framework}")
            
            # Search for compatibility information
            compatibility_query = f"{package_name} {target_framework} compatibility {current_version}"
            compatibility_results = self.search(compatibility_query, num_results=5)
            
            # Search for vulnerability information
            vulnerability_query = f"{package_name} {current_version} vulnerabilities CVE"
            vulnerability_results = self.search(vulnerability_query, num_results=5)
            
            # Extract compatibility information
            compatibility_info = self._extract_compatibility_info(
                compatibility_results.get("results", []),
                package_name,
                target_framework
            )
            
            # Extract vulnerability information
            vulnerability_info = self._extract_vulnerability_info(
                vulnerability_results.get("results", []),
                package_name,
                current_version
            )
            
            # Get latest version information
            latest_version_query = f"{package_name} latest version"
            latest_version_results = self.search(latest_version_query, num_results=3)
            latest_version = self._extract_latest_version(
                latest_version_results.get("results", []),
                package_name
            )
            
            return {
                "status": "success",
                "package_name": package_name,
                "current_version": current_version,
                "target_framework": target_framework,
                "compatibility": compatibility_info,
                "vulnerabilities": vulnerability_info,
                "latest_version": latest_version,
                "last_checked": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking package compatibility: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to check compatibility: {str(e)}"
            }

    def _extract_compatibility_info(self, results: List[Dict], package_name: str, 
                                  target_framework: str) -> Dict:
        """Extract compatibility information from search results."""
        compatibility_info = {
            "is_compatible": False,
            "evidence": [],
            "recommendations": []
        }
        
        for result in results:
            text = f"{result['title']} {result['snippet']}".lower()
            
            # Check for compatibility mentions
            if (package_name.lower() in text and 
                target_framework.lower() in text):
                
                # Look for compatibility indicators
                if any(indicator in text for indicator in [
                    "compatible", "supported", "works with", "runs on"
                ]):
                    compatibility_info["is_compatible"] = True
                    compatibility_info["evidence"].append({
                        "source": result["link"],
                        "text": result["snippet"]
                    })
                
                # Look for recommendations
                if "recommend" in text or "suggest" in text:
                    compatibility_info["recommendations"].append({
                        "source": result["link"],
                        "text": result["snippet"]
                    })
        
        return compatibility_info

    def _extract_vulnerability_info(self, results: List[Dict], package_name: str, 
                                  version: str) -> Dict:
        """Extract vulnerability information from search results."""
        vulnerabilities = []
        
        for result in results:
            text = f"{result['title']} {result['snippet']}"
            
            # Look for CVE references
            cve_matches = re.findall(r'CVE-\d{4}-\d{4,7}', text)
            
            if cve_matches:
                for cve in cve_matches:
                    vulnerabilities.append({
                        "id": cve,
                        "source": result["link"],
                        "description": result["snippet"],
                        "severity": self._extract_severity(text)
                    })
        
        return {
            "has_vulnerabilities": len(vulnerabilities) > 0,
            "vulnerabilities": vulnerabilities
        }

    def _extract_latest_version(self, results: List[Dict], package_name: str) -> str:
        """Extract the latest version from search results."""
        versions = set()
        
        for result in results:
            text = f"{result['title']} {result['snippet']}"
            
            # Look for version numbers
            version_matches = re.findall(r'\d+\.\d+\.\d+', text)
            versions.update(version_matches)
        
        if versions:
            return max(versions, key=lambda x: tuple(map(int, x.split('.'))))
        return "unknown"

    def _extract_severity(self, text: str) -> str:
        """Extract vulnerability severity from text."""
        text = text.lower()
        if "critical" in text:
            return "critical"
        elif "high" in text:
            return "high"
        elif "medium" in text:
            return "medium"
        elif "low" in text:
            return "low"
        return "unknown"

    def check_maven_compatibility(self, group_id: str, artifact_id: str, 
                                current_version: str, target_runtime: str) -> Dict:
        """Check Maven package compatibility and vulnerabilities.
        
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
            
            # Search for compatibility information
            compatibility_query = f"{group_id} {artifact_id} {target_runtime} compatibility {current_version} maven"
            compatibility_results = self.search(compatibility_query, num_results=5)
            
            # Search for vulnerability information
            vulnerability_query = f"{group_id} {artifact_id} {current_version} vulnerabilities CVE"
            vulnerability_results = self.search(vulnerability_query, num_results=5)
            
            # Extract compatibility information
            compatibility_info = self._extract_java_compatibility_info(
                compatibility_results.get("results", []),
                f"{group_id}:{artifact_id}",
                target_runtime
            )
            
            # Extract vulnerability information
            vulnerability_info = self._extract_vulnerability_info(
                vulnerability_results.get("results", []),
                f"{group_id}:{artifact_id}",
                current_version
            )
            
            # Get latest version information
            latest_version_query = f"{group_id} {artifact_id} latest version maven"
            latest_version_results = self.search(latest_version_query, num_results=3)
            latest_version = self._extract_latest_version(
                latest_version_results.get("results", []),
                f"{group_id}:{artifact_id}"
            )
            
            return {
                "status": "success",
                "group_id": group_id,
                "artifact_id": artifact_id,
                "current_version": current_version,
                "target_runtime": target_runtime,
                "compatibility": compatibility_info,
                "vulnerabilities": vulnerability_info,
                "latest_version": latest_version,
                "last_checked": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking Maven compatibility: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to check compatibility: {str(e)}"
            }

    def check_gradle_compatibility(self, group_id: str, artifact_id: str, 
                                 current_version: str, target_runtime: str) -> Dict:
        """Check Gradle package compatibility and vulnerabilities.
        
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
            
            # Search for compatibility information
            compatibility_query = f"{group_id} {artifact_id} {target_runtime} compatibility {current_version} gradle"
            compatibility_results = self.search(compatibility_query, num_results=5)
            
            # Search for vulnerability information
            vulnerability_query = f"{group_id} {artifact_id} {current_version} vulnerabilities CVE"
            vulnerability_results = self.search(vulnerability_query, num_results=5)
            
            # Extract compatibility information
            compatibility_info = self._extract_java_compatibility_info(
                compatibility_results.get("results", []),
                f"{group_id}:{artifact_id}",
                target_runtime
            )
            
            # Extract vulnerability information
            vulnerability_info = self._extract_vulnerability_info(
                vulnerability_results.get("results", []),
                f"{group_id}:{artifact_id}",
                current_version
            )
            
            # Get latest version information
            latest_version_query = f"{group_id} {artifact_id} latest version gradle"
            latest_version_results = self.search(latest_version_query, num_results=3)
            latest_version = self._extract_latest_version(
                latest_version_results.get("results", []),
                f"{group_id}:{artifact_id}"
            )
            
            return {
                "status": "success",
                "group_id": group_id,
                "artifact_id": artifact_id,
                "current_version": current_version,
                "target_runtime": target_runtime,
                "compatibility": compatibility_info,
                "vulnerabilities": vulnerability_info,
                "latest_version": latest_version,
                "last_checked": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking Gradle compatibility: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to check compatibility: {str(e)}"
            }

    def _extract_java_compatibility_info(self, results: List[Dict], package_name: str, 
                                       target_runtime: str) -> Dict:
        """Extract Java compatibility information from search results."""
        compatibility_info = {
            "is_compatible": False,
            "evidence": [],
            "recommendations": [],
            "supported_runtimes": set()  # We'll convert this to a list before returning
        }
        
        for result in results:
            text = f"{result['title']} {result['snippet']}".lower()
            
            # Check for compatibility mentions
            if package_name.lower() in text:
                # Look for runtime compatibility
                for runtime in self.JAVA_RUNTIME_COMPATIBILITY.keys():
                    if runtime in text:
                        compatibility_info["supported_runtimes"].add(runtime)
                
                # Check if target runtime is compatible
                if target_runtime.lower() in text:
                    if any(indicator in text for indicator in [
                        "compatible", "supported", "works with", "runs on"
                    ]):
                        compatibility_info["is_compatible"] = True
                        compatibility_info["evidence"].append({
                            "source": result["link"],
                            "text": result["snippet"]
                        })
                
                # Look for recommendations
                if "recommend" in text or "suggest" in text:
                    compatibility_info["recommendations"].append({
                        "source": result["link"],
                        "text": result["snippet"]
                    })
        
        # Check runtime compatibility chain
        if not compatibility_info["is_compatible"]:
            target_runtime = target_runtime.lower()
            for runtime in compatibility_info["supported_runtimes"]:
                if runtime in self.JAVA_RUNTIME_COMPATIBILITY.get(target_runtime, []):
                    compatibility_info["is_compatible"] = True
                    break
        
        # Convert set to list for JSON serialization
        compatibility_info["supported_runtimes"] = sorted(list(compatibility_info["supported_runtimes"]))
        
        return compatibility_info 