"""NuGet API client for package management operations."""

import logging
import requests
from typing import Dict, List, Optional, Set
from datetime import datetime
from urllib.parse import quote
from packaging.version import Version, InvalidVersion

logger = logging.getLogger(__name__)

class NuGetAPI:
    """Client for interacting with the NuGet API."""
    
    BASE_URL = "https://api.nuget.org/v3/index.json"
    SEARCH_URL = "https://azuresearch-usnc.nuget.org/query"
    PACKAGE_URL = "https://api.nuget.org/v3/registration5-gz-semver2/{package_id}/index.json"
    VULNERABILITY_URL = "https://api.nuget.org/v3/catalog0/data/{package_id}/{version}.json"
    FLAT_CONTAINER_URL = "https://api.nuget.org/v3-flatcontainer/{package}/index.json"
    REGISTRATION_URL = "https://api.nuget.org/v3/registration5-gz-semver2/{package}/index.json"

    # Framework compatibility mapping
    FRAMEWORK_COMPATIBILITY = {
        "netstandard1.0": ["net45", "net40", "net35", "net20"],
        "netstandard1.1": ["net45", "net40", "net35", "net20"],
        "netstandard1.2": ["net45", "net40", "net35", "net20"],
        "netstandard1.3": ["net45", "net40", "net35", "net20"],
        "netstandard1.4": ["net45", "net40", "net35", "net20"],
        "netstandard1.5": ["net45", "net40", "net35", "net20"],
        "netstandard1.6": ["net45", "net40", "net35", "net20"],
        "netstandard2.0": ["net48", "net472", "net471", "net47", "net462", "net461", "net46", "net452", "net451", "net45", "net40", "net35", "net20"],
        "netstandard2.1": ["net48", "net472", "net471", "net47", "net462", "net461", "net46", "net452", "net451", "net45", "net40", "net35", "net20"],
        "net6.0": ["net48", "net472", "net471", "net47", "net462", "net461", "net46", "net452", "net451", "net45", "net40", "net35", "net20"],
        "net7.0": ["net48", "net472", "net471", "net47", "net462", "net461", "net46", "net452", "net451", "net45", "net40", "net35", "net20"],
        "net8.0": ["net48", "net472", "net471", "net47", "net462", "net461", "net46", "net452", "net451", "net45", "net40", "net35", "net20"],
        "net48": ["net48", "net472", "net471", "net47", "net462", "net461", "net46", "net452", "net451", "net45", "net40", "net35", "net20"],
        "net472": ["net472", "net471", "net47", "net462", "net461", "net46", "net452", "net451", "net45", "net40", "net35", "net20"],
        "net471": ["net471", "net47", "net462", "net461", "net46", "net452", "net451", "net45", "net40", "net35", "net20"],
        "net47": ["net47", "net462", "net461", "net46", "net452", "net451", "net45", "net40", "net35", "net20"],
        "net462": ["net462", "net461", "net46", "net452", "net451", "net45", "net40", "net35", "net20"],
        "net461": ["net461", "net46", "net452", "net451", "net45", "net40", "net35", "net20"],
        "net46": ["net46", "net452", "net451", "net45", "net40", "net35", "net20"],
        "net452": ["net452", "net451", "net45", "net40", "net35", "net20"],
        "net451": ["net451", "net45", "net40", "net35", "net20"],
        "net45": ["net45", "net40", "net35", "net20"],
        "net40": ["net40", "net35", "net20"],
        "net35": ["net35", "net20"],
        "net20": ["net20"]
    }

    def __init__(self):
        """Initialize the NuGet API client."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "DevFlow-Package-Management/1.0",
            "Accept": "application/json"
        })

    def get_package_versions(self, package_id: str) -> Dict:
        """Get all available versions of a package.
        
        Args:
            package_id: The package identifier
            
        Returns:
            Dict containing package versions and metadata
        """
        try:
            url = self.PACKAGE_URL.format(package_id=quote(package_id.lower()))
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            versions = []
            
            for entry in data.get("items", []):
                for version in entry.get("items", []):
                    version_data = version.get("catalogEntry", {})
                    versions.append({
                        "version": version_data.get("version"),
                        "published": version_data.get("published"),
                        "downloads": version_data.get("downloads", 0)
                    })
            
            return {
                "status": "success",
                "package_id": package_id,
                "versions": sorted(versions, key=lambda x: x["version"], reverse=True)
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching package versions: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to fetch versions: {str(e)}"
            }

    def get_compatible_versions(self, package_id: str, target_framework: str, 
                              current_version: Optional[str] = None) -> Dict:
        """Get versions compatible with a specific target framework.
        
        Args:
            package_id: The package identifier
            target_framework: Target .NET framework (e.g., "net45", "netstandard2.0")
            current_version: Current package version (optional)
            
        Returns:
            Dict containing compatible versions and metadata
        """
        try:
            logger.info(f"Checking compatibility for {package_id} with framework {target_framework}")
            
            # Normalize target framework
            target_framework = self._normalize_framework(target_framework)
            
            url = self.PACKAGE_URL.format(package_id=quote(package_id.lower()))
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            compatible_versions = []
            version_details = []
            
            # Process each version entry
            for entry in data.get("items", []):
                for version_entry in entry.get("items", []):
                    version_data = version_entry.get("catalogEntry", {})
                    version = version_data.get("version")
                    
                    # Skip if version is invalid
                    try:
                        Version(version)
                    except InvalidVersion:
                        logger.warning(f"Skipping invalid version {version} for {package_id}")
                        continue
                    
                    # Get framework groups for this version
                    framework_groups = version_data.get("dependencyGroups", [])
                    supported_frameworks = self._get_supported_frameworks(framework_groups)
                    
                    # Check compatibility
                    if self._is_framework_compatible(target_framework, supported_frameworks):
                        version_info = {
                            "version": version,
                            "published": version_data.get("published"),
                            "downloads": version_data.get("downloads", 0),
                            "supported_frameworks": supported_frameworks
                        }
                        compatible_versions.append(version)
                        version_details.append(version_info)
            
            # Sort versions by version number
            compatible_versions.sort(key=Version, reverse=True)
            version_details.sort(key=lambda x: Version(x["version"]), reverse=True)
            
            result = {
                "status": "success",
                "package_id": package_id,
                "target_framework": target_framework,
                "compatible_versions": compatible_versions,
                "latest_compatible": compatible_versions[0] if compatible_versions else None,
                "version_details": version_details
            }
            
            logger.info(f"Found {len(compatible_versions)} compatible versions for {package_id}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching compatible versions: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to fetch compatible versions: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error in get_compatible_versions: {str(e)}")
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }

    def _normalize_framework(self, framework: str) -> str:
        """Normalize framework name to standard format."""
        framework = framework.lower().replace('.', '').replace('-', '')
        if framework.startswith('net'):
            return framework
        return f"net{framework}"

    def _get_supported_frameworks(self, dependency_groups: List[Dict]) -> Set[str]:
        """Extract supported frameworks from dependency groups."""
        frameworks = set()
        for group in dependency_groups:
            framework = group.get("targetFramework", "")
            if framework:
                frameworks.add(self._normalize_framework(framework))
        return frameworks

    def _is_framework_compatible(self, target: str, supported: Set[str]) -> bool:
        """Check if target framework is compatible with supported frameworks."""
        target = self._normalize_framework(target)
        
        # Direct match
        if target in supported:
            return True
            
        # Check framework compatibility mapping
        for framework, compatible_frameworks in self.FRAMEWORK_COMPATIBILITY.items():
            if target in compatible_frameworks:
                # If any of the compatible frameworks are supported, return true
                if any(f in supported for f in compatible_frameworks):
                    return True
                    
        return False

    def get_package_dependencies(self, package_id: str, version: str, 
                               target_framework: str) -> Dict:
        """Get dependencies for a specific package version.
        
        Args:
            package_id: The package identifier
            version: Package version
            target_framework: Target .NET framework
            
        Returns:
            Dict containing package dependencies
        """
        try:
            url = self.PACKAGE_URL.format(package_id=quote(package_id.lower()))
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            dependencies = []
            
            for entry in data.get("items", []):
                for version_entry in entry.get("items", []):
                    if version_entry.get("catalogEntry", {}).get("version") == version:
                        for group in version_entry.get("catalogEntry", {}).get("dependencyGroups", []):
                            if group.get("targetFramework") == target_framework:
                                for dep in group.get("dependencies", []):
                                    dependencies.append({
                                        "id": dep.get("id"),
                                        "version_range": dep.get("range"),
                                        "type": "direct"
                                    })
            
            return {
                "status": "success",
                "package_id": package_id,
                "version": version,
                "target_framework": target_framework,
                "dependencies": dependencies
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching dependencies: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to fetch dependencies: {str(e)}"
            }

    def check_package_vulnerabilities(self, package_id: str, version: str) -> Dict:
        """Check for known vulnerabilities in a package version.
        
        Args:
            package_id: The package identifier
            version: Package version
            
        Returns:
            Dict containing vulnerability information
        """
        try:
            # Note: This is a simplified implementation. In a real scenario,
            # you would integrate with a vulnerability database like OSS Index
            # or GitHub Security Advisories.
            url = self.VULNERABILITY_URL.format(
                package_id=quote(package_id.lower()),
                version=quote(version)
            )
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            vulnerabilities = []
            
            # Check for known vulnerabilities (this is a placeholder)
            # In a real implementation, you would check against a vulnerability database
            if package_id.lower() == "newtonsoft.json" and version == "9.0.1":
                vulnerabilities.append({
                    "id": "CVE-2023-1234",
                    "severity": "high",
                    "description": "Deserialization vulnerability in Newtonsoft.Json 9.0.1",
                    "affected_versions": ["9.0.1"],
                    "fixed_versions": ["13.0.1"]
                })
            
            return {
                "status": "success",
                "package_id": package_id,
                "version": version,
                "vulnerabilities": vulnerabilities,
                "last_checked": datetime.utcnow().isoformat()
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking vulnerabilities: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to check vulnerabilities: {str(e)}"
            }

    def get_package_metadata(self, package_id: str, version: str) -> Dict:
        """Get comprehensive metadata for a package version.
        
        Args:
            package_id: The package identifier
            version: Package version
            
        Returns:
            Dict containing package metadata
        """
        try:
            url = self.PACKAGE_URL.format(package_id=quote(package_id.lower()))
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            metadata = {}
            
            for entry in data.get("items", []):
                for version_entry in entry.get("items", []):
                    if version_entry.get("catalogEntry", {}).get("version") == version:
                        catalog_entry = version_entry.get("catalogEntry", {})
                        metadata = {
                            "id": catalog_entry.get("id"),
                            "version": catalog_entry.get("version"),
                            "authors": catalog_entry.get("authors", []),
                            "description": catalog_entry.get("description"),
                            "project_url": catalog_entry.get("projectUrl"),
                            "license_url": catalog_entry.get("licenseUrl"),
                            "tags": catalog_entry.get("tags", []),
                            "published": catalog_entry.get("published"),
                            "downloads": catalog_entry.get("downloads", 0)
                        }
                        break
            
            return {
                "status": "success",
                "package_id": package_id,
                "version": version,
                "metadata": metadata
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching metadata: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to fetch metadata: {str(e)}"
            }

    def get_latest_compatible_version(self, package_id: str, target_framework: str) -> dict:
        """
        Get the latest version of a NuGet package compatible with the given target framework.
        """
        try:
            versions = self._fetch_all_versions(package_id)
            if not versions:
                logger.warning(f"No versions found for package {package_id}")
                return {"status": "error", "message": "No versions found."}

            metadata = self._fetch_metadata(package_id)
            compatible_versions = self._find_compatible_versions(metadata, target_framework)
            if not compatible_versions:
                logger.info(f"No compatible versions found for {package_id} and {target_framework}")
                return {"status": "error", "message": "No compatible versions found."}

            latest = max(compatible_versions, key=Version)
            logger.info(f"Latest compatible version for {package_id} and {target_framework}: {latest}")
            return {
                "status": "success",
                "package_id": package_id,
                "target_framework": target_framework,
                "latest_compatible": latest,
                "compatible_versions": sorted(compatible_versions, key=Version, reverse=True)
            }
        except Exception as e:
            logger.error(f"Error in get_latest_compatible_version: {e}")
            return {"status": "error", "message": str(e)}

    def _fetch_all_versions(self, package_id: str):
        url = self.FLAT_CONTAINER_URL.format(package=package_id.lower())
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json().get("versions", [])

    def _fetch_metadata(self, package_id: str):
        url = self.REGISTRATION_URL.format(package=package_id.lower())
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()

    def _find_compatible_versions(self, metadata, target_framework):
        compatible = []
        norm_target = target_framework.lower().replace('.', '').replace('-', '')
        for entry in metadata.get("items", []):
            for version_entry in entry.get("items", []):
                version = version_entry.get("catalogEntry", {}).get("version")
                groups = version_entry.get("catalogEntry", {}).get("dependencyGroups", [])
                for group in groups:
                    api_framework = group.get("targetFramework", "")
                    norm_api_framework = api_framework.lower().replace('.', '').replace('-', '')
                    if norm_target in norm_api_framework or norm_api_framework in norm_target:
                        compatible.append(version)
                        break 