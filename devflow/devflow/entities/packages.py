"""Package entity module for representing software packages and their metadata."""

from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


class PackageManagerType(str, Enum):
    """Enum representing different package managers."""
    NPM = "npm"
    PIP = "pip"
    MAVEN = "maven"
    GRADLE = "gradle"
    NUGET = "nuget"
    COMPOSER = "composer"
    GEM = "gem"
    CARGO = "cargo"
    GO_MOD = "go_mod"
    YARN = "yarn"
    PNPM = "pnpm"


class ProgrammingLanguage(str, Enum):
    """Enum representing different programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CSHARP = "csharp"
    PHP = "php"
    RUBY = "ruby"
    RUST = "rust"
    GO = "go"
    TYPESCRIPT = "typescript"


class License(BaseModel):
    """Represents a software license."""
    name: str
    identifier: str
    url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class Dependency(BaseModel):
    """Represents a package dependency."""
    name: str
    version: str
    is_dev_dependency: bool = False
    is_optional: bool = False
    model_config = ConfigDict(from_attributes=True)


class Vulnerability(BaseModel):
    """Represents a security vulnerability in a package."""
    id: str
    severity: str
    description: str
    affected_versions: List[str]
    fixed_version: Optional[str] = None
    published_date: datetime
    model_config = ConfigDict(from_attributes=True)


class PackageMetadata(BaseModel):
    """Represents metadata about a package."""
    description: str
    keywords: List[str] = Field(default_factory=list)
    author: Optional[str] = None
    maintainers: List[str] = Field(default_factory=list)
    repository: Optional[str] = None
    homepage: Optional[str] = None
    documentation: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class Package(BaseModel):
    """
    Represents a software package with its dependencies and metadata.
    This entity is designed to be flexible enough to work with different
    programming languages and package managers.
    """

    name: str
    version: str
    package_manager: PackageManagerType
    language: ProgrammingLanguage
    metadata: PackageMetadata
    dependencies: List[Dependency] = Field(default_factory=list)
    dev_dependencies: List[Dependency] = Field(default_factory=list)
    optional_dependencies: List[Dependency] = Field(default_factory=list)
    license: License
    vulnerabilities: List[Vulnerability] = Field(default_factory=list)
    last_updated: datetime
    download_count: Optional[int] = None
    size: Optional[int] = None  # Size in bytes
    checksum: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    def to_json(self) -> str:
        """
        Converts the Package object to a JSON string.

        Returns:
            A JSON string representing the Package object.
        """
        return self.model_dump_json(indent=4)

    def get_all_dependencies(self) -> List[Dependency]:
        """
        Returns a combined list of all dependencies (regular, dev, and optional).

        Returns:
            List of all dependencies.
        """
        return self.dependencies + self.dev_dependencies + self.optional_dependencies

    def has_vulnerabilities(self) -> bool:
        """
        Checks if the package has any known vulnerabilities.

        Returns:
            True if vulnerabilities exist, False otherwise.
        """
        return len(self.vulnerabilities) > 0

    def get_latest_version(self) -> str:
        """
        In a real implementation, this would fetch the latest version from the package registry.
        For demonstration purposes, returns the current version.

        Returns:
            The latest version of the package.
        """
        return self.version

    @staticmethod
    def get_package(package_name: str, package_manager: PackageManagerType) -> Optional["Package"]:
        """
        Retrieves a package based on its name and package manager.

        Args:
            package_name: The name of the package to retrieve.
            package_manager: The package manager type.

        Returns:
            The Package object if found, None otherwise.
        """
        # In a real application, this would involve a package registry lookup.
        # For this example, we'll return a dummy package.
        return Package(
            name=package_name,
            version="1.0.0",
            package_manager=package_manager,
            language=ProgrammingLanguage.PYTHON,
            metadata=PackageMetadata(
                description="A sample package for demonstration purposes",
                keywords=["sample", "demo"],
                author="Sample Author",
                maintainers=["Maintainer 1", "Maintainer 2"],
                repository="https://github.com/example/sample-package",
                homepage="https://example.com/sample-package",
                documentation="https://example.com/sample-package/docs"
            ),
            dependencies=[
                Dependency(name="requests", version="2.31.0", is_dev_dependency=False),
                Dependency(name="pydantic", version="2.5.2", is_dev_dependency=False)
            ],
            dev_dependencies=[
                Dependency(name="pytest", version="7.4.3", is_dev_dependency=True),
                Dependency(name="black", version="23.11.0", is_dev_dependency=True)
            ],
            optional_dependencies=[
                Dependency(name="uvicorn", version="0.24.0", is_optional=True)
            ],
            license=License(
                name="MIT License",
                identifier="MIT",
                url="https://opensource.org/licenses/MIT"
            ),
            vulnerabilities=[],
            last_updated=datetime.now(),
            download_count=1000,
            size=1024 * 1024,  # 1MB
            checksum="sha256:abc123..."
        )
