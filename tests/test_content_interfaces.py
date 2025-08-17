"""
Test suite for IContentProvider and IBacklinkService interfaces.
Tests follow strict TDD principles and must fail initially.
"""

import pytest
from typing import List, Dict, Optional, Any
import inspect
import asyncio
from abc import ABC


class TestContentProviderInterface:
    """Test IContentProvider interface requirements."""

    def test_content_provider_interface_exists(self):
        """Test 1: Verify IContentProvider abstract base class exists."""
        try:
            from app.interfaces import IContentProvider

            assert issubclass(IContentProvider, ABC), (
                "IContentProvider should inherit from ABC"
            )
        except ImportError:
            pytest.fail("IContentProvider interface should exist")

    def test_content_provider_required_methods(self):
        """Test 2: Verify interface defines required methods."""
        try:
            from app.interfaces import IContentProvider

            # Check required methods exist
            required_methods = [
                "get_content_by_slug",
                "get_all_content",
                "get_content_by_tag",
            ]

            for method_name in required_methods:
                assert hasattr(IContentProvider, method_name), (
                    f"IContentProvider should have {method_name} method"
                )

                # Verify methods are abstract
                method = getattr(IContentProvider, method_name)
                assert hasattr(method, "__isabstractmethod__"), (
                    f"{method_name} should be abstract"
                )
                assert method.__isabstractmethod__, (
                    f"{method_name} should be marked as abstract"
                )

        except ImportError:
            pytest.fail("IContentProvider interface should exist")

    def test_interfaces_are_abstract(self):
        """Test 5: Verify interfaces cannot be instantiated directly."""
        try:
            from app.interfaces import IContentProvider

            # Attempt to instantiate should raise TypeError
            with pytest.raises(TypeError, match="Can't instantiate abstract class"):
                IContentProvider()

        except ImportError:
            pytest.fail("IContentProvider interface should exist")

    def test_content_provider_has_all_methods(self):
        """Test that IContentProvider has all required methods from planning phase."""
        try:
            from app.interfaces import IContentProvider

            all_methods = [
                "get_content",
                "get_bookmarks",
                "get_posts_by_tag",
                "get_mixed_content",  # Should be async
                "get_tag_counts",
                "get_til_posts",
                "get_til_posts_by_tag",
                "render_markdown",
                "get_homepage_sections",  # Should be async
                "get_all_garden_content",
                "get_content_by_slug",  # User required
                "get_all_content",  # User required
                "get_content_by_tag",  # User required
            ]

            for method_name in all_methods:
                assert hasattr(IContentProvider, method_name), (
                    f"IContentProvider should have {method_name} method"
                )

        except ImportError:
            pytest.fail("IContentProvider interface should exist")

    def test_content_provider_async_methods(self):
        """Test that specified methods are async."""
        try:
            from app.interfaces import IContentProvider

            async_methods = ["get_mixed_content", "get_homepage_sections"]

            for method_name in async_methods:
                method = getattr(IContentProvider, method_name)
                # Check if method is a coroutine function
                assert asyncio.iscoroutinefunction(
                    method
                ) or inspect.iscoroutinefunction(method), (
                    f"{method_name} should be async"
                )

        except ImportError:
            pytest.fail("IContentProvider interface should exist")


class TestBacklinkServiceInterface:
    """Test IBacklinkService interface requirements."""

    def test_backlink_service_interface_exists(self):
        """Test 3: Verify IBacklinkService abstract base class exists."""
        try:
            from app.interfaces import IBacklinkService

            assert issubclass(IBacklinkService, ABC), (
                "IBacklinkService should inherit from ABC"
            )
        except ImportError:
            pytest.fail("IBacklinkService interface should exist")

    def test_backlink_service_required_methods(self):
        """Test 4: Verify interface defines required methods."""
        try:
            from app.interfaces import IBacklinkService

            # Check required methods exist
            required_methods = ["get_backlinks", "extract_internal_links"]

            for method_name in required_methods:
                assert hasattr(IBacklinkService, method_name), (
                    f"IBacklinkService should have {method_name} method"
                )

                # Verify methods are abstract
                method = getattr(IBacklinkService, method_name)
                assert hasattr(method, "__isabstractmethod__"), (
                    f"{method_name} should be abstract"
                )
                assert method.__isabstractmethod__, (
                    f"{method_name} should be marked as abstract"
                )

        except ImportError:
            pytest.fail("IBacklinkService interface should exist")

    def test_backlink_service_cannot_be_instantiated(self):
        """Test that IBacklinkService cannot be instantiated."""
        try:
            from app.interfaces import IBacklinkService

            with pytest.raises(TypeError, match="Can't instantiate abstract class"):
                IBacklinkService()

        except ImportError:
            pytest.fail("IBacklinkService interface should exist")

    def test_backlink_service_has_all_methods(self):
        """Test that IBacklinkService has all required methods from planning phase."""
        try:
            from app.interfaces import IBacklinkService

            all_methods = [
                "extract_internal_links",  # User required
                "get_backlinks",  # User required
                "get_forward_links",
                "build_link_graph",
                "validate_links",
                "get_orphaned_content",
                "refresh_cache",
            ]

            for method_name in all_methods:
                assert hasattr(IBacklinkService, method_name), (
                    f"IBacklinkService should have {method_name} method"
                )

        except ImportError:
            pytest.fail("IBacklinkService interface should exist")


class TestInterfaceContract:
    """Test interface method signatures and contracts."""

    def test_interface_method_signatures(self):
        """Test 6: Verify methods have correct type hints and return types."""
        try:
            from app.interfaces import IContentProvider, IBacklinkService

            # Test IContentProvider method signatures
            content_provider_methods = {
                "get_content_by_slug": {
                    "params": ["content_type", "slug"],
                    "return": "Optional[Dict[str, Any]]",
                },
                "get_all_content": {"params": [], "return": "List[Dict[str, Any]]"},
                "get_content_by_tag": {
                    "params": ["tag"],
                    "return": "List[Dict[str, Any]]",
                },
            }

            for method_name, expected in content_provider_methods.items():
                method = getattr(IContentProvider, method_name)
                sig = inspect.signature(method)

                # Check parameters exist (excluding self)
                params = list(sig.parameters.keys())
                if "self" in params:
                    params.remove("self")

                for param in expected["params"]:
                    assert param in params, (
                        f"{method_name} should have parameter {param}"
                    )

                # Check return annotation exists
                assert sig.return_annotation != inspect.Signature.empty, (
                    f"{method_name} should have return type annotation"
                )

            # Test IBacklinkService method signatures
            backlink_methods = {
                "get_backlinks": {
                    "params": ["target_slug"],
                    "return": "List[Dict[str, str]]",
                },
                "extract_internal_links": {
                    "params": ["content", "content_path"],
                    "return": "Set[str]",
                },
            }

            for method_name, expected in backlink_methods.items():
                method = getattr(IBacklinkService, method_name)
                sig = inspect.signature(method)

                # Check parameters exist (excluding self)
                params = list(sig.parameters.keys())
                if "self" in params:
                    params.remove("self")

                for param in expected["params"]:
                    assert param in params, (
                        f"{method_name} should have parameter {param}"
                    )

                # Check return annotation exists
                assert sig.return_annotation != inspect.Signature.empty, (
                    f"{method_name} should have return type annotation"
                )

        except ImportError:
            pytest.fail("Interfaces should exist")

    def test_type_hints_use_proper_imports(self):
        """Test that type hints use proper typing module imports."""
        try:
            import app.interfaces as interfaces_module

            # Check that typing imports are present
            module_dict = vars(interfaces_module)

            expected_imports = ["List", "Dict", "Optional", "Any"]
            for import_name in expected_imports:
                assert import_name in module_dict or hasattr(
                    interfaces_module, import_name
                ), f"interfaces module should import {import_name} from typing"

        except ImportError:
            pytest.fail("Interfaces module should exist")


class TestInterfaceUsage:
    """Test interface usage patterns."""

    def test_concrete_implementation_works(self):
        """Test that a concrete implementation of interfaces works."""
        try:
            from app.interfaces import IContentProvider

            # Create a concrete implementation
            class ConcreteContentProvider(IContentProvider):
                def get_content_by_slug(
                    self, content_type: str, slug: str
                ) -> Optional[Dict[str, Any]]:
                    return {"type": content_type, "slug": slug}

                def get_all_content(self) -> List[Dict[str, Any]]:
                    return []

                def get_content_by_tag(self, tag: str) -> List[Dict[str, Any]]:
                    return []

                def get_content(
                    self, content_type: str, limit: Optional[int] = None
                ) -> Dict[str, Any]:
                    return {"content": [], "total": 0}

                def get_bookmarks(
                    self, limit: Optional[int] = 10
                ) -> List[Dict[str, Any]]:
                    return []

                def get_posts_by_tag(
                    self, tag: str, content_types: Optional[List[str]] = None
                ) -> Dict[str, Any]:
                    return {"posts": [], "tag": tag}

                async def get_mixed_content(
                    self, page: int = 1, per_page: int = 10
                ) -> Dict[str, Any]:
                    return {"content": [], "page": page}

                def get_tag_counts(self) -> Dict[str, int]:
                    return {}

                def get_til_posts(
                    self, page: int = 1, per_page: int = 30
                ) -> Dict[str, Any]:
                    return {"posts": [], "page": page}

                def get_til_posts_by_tag(self, tag: str) -> List[Dict[str, Any]]:
                    return []

                def render_markdown(self, file_path: str) -> Dict[str, Any]:
                    return {"content": "", "metadata": {}}

                async def get_homepage_sections(self) -> Dict[str, Any]:
                    return {"sections": []}

                def get_all_garden_content(self) -> Dict[str, Any]:
                    return {"content": []}

            # Should be able to instantiate concrete class
            provider = ConcreteContentProvider()
            assert isinstance(provider, IContentProvider)

            # Methods should work
            result = provider.get_content_by_slug("notes", "test")
            assert result == {"type": "notes", "slug": "test"}

        except ImportError:
            pytest.fail("IContentProvider interface should exist")

    def test_incomplete_implementation_fails(self):
        """Test that incomplete implementation raises TypeError."""
        try:
            from app.interfaces import IContentProvider

            # Create incomplete implementation
            class IncompleteProvider(IContentProvider):
                def get_content_by_slug(
                    self, content_type: str, slug: str
                ) -> Optional[Dict[str, Any]]:
                    return None

                # Missing other required methods

            # Should not be able to instantiate incomplete class
            with pytest.raises(TypeError, match="Can't instantiate abstract class"):
                IncompleteProvider()

        except ImportError:
            pytest.fail("IContentProvider interface should exist")

    def test_multiple_interface_implementation(self):
        """Test that a class can implement multiple interfaces."""
        try:
            from app.interfaces import IContentProvider, IBacklinkService

            # Create a class implementing both interfaces
            class UnifiedService(IContentProvider, IBacklinkService):
                # IContentProvider methods
                def get_content_by_slug(
                    self, content_type: str, slug: str
                ) -> Optional[Dict[str, Any]]:
                    return None

                def get_all_content(self) -> List[Dict[str, Any]]:
                    return []

                def get_content_by_tag(self, tag: str) -> List[Dict[str, Any]]:
                    return []

                def get_content(
                    self, content_type: str, limit: Optional[int] = None
                ) -> Dict[str, Any]:
                    return {"content": []}

                def get_bookmarks(
                    self, limit: Optional[int] = 10
                ) -> List[Dict[str, Any]]:
                    return []

                def get_posts_by_tag(
                    self, tag: str, content_types: Optional[List[str]] = None
                ) -> Dict[str, Any]:
                    return {"posts": []}

                async def get_mixed_content(
                    self, page: int = 1, per_page: int = 10
                ) -> Dict[str, Any]:
                    return {"content": []}

                def get_tag_counts(self) -> Dict[str, int]:
                    return {}

                def get_til_posts(
                    self, page: int = 1, per_page: int = 30
                ) -> Dict[str, Any]:
                    return {"posts": []}

                def get_til_posts_by_tag(self, tag: str) -> List[Dict[str, Any]]:
                    return []

                def render_markdown(self, file_path: str) -> Dict[str, Any]:
                    return {"content": ""}

                async def get_homepage_sections(self) -> Dict[str, Any]:
                    return {"sections": []}

                def get_all_garden_content(self) -> Dict[str, Any]:
                    return {"content": []}

                # IBacklinkService methods
                def extract_internal_links(
                    self, content: str, content_path: str
                ) -> set:
                    return set()

                def get_backlinks(self, target_slug: str) -> List[Dict[str, str]]:
                    return []

                def get_forward_links(self, source_slug: str) -> List[Dict[str, str]]:
                    return []

                def build_link_graph(self) -> Dict[str, List[str]]:
                    return {}

                def validate_links(self) -> List[Dict[str, str]]:
                    return []

                def get_orphaned_content(self) -> List[str]:
                    return []

                def refresh_cache(self) -> None:
                    pass

            # Should be able to instantiate
            service = UnifiedService()
            assert isinstance(service, IContentProvider)
            assert isinstance(service, IBacklinkService)

        except ImportError:
            pytest.fail("Interfaces should exist")


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_abstract_methods_have_docstrings(self):
        """Test that abstract methods have proper documentation."""
        try:
            from app.interfaces import IContentProvider, IBacklinkService

            # Check IContentProvider methods have docstrings
            for method_name in [
                "get_content_by_slug",
                "get_all_content",
                "get_content_by_tag",
            ]:
                method = getattr(IContentProvider, method_name)
                assert method.__doc__ is not None, (
                    f"{method_name} should have a docstring"
                )
                assert len(method.__doc__.strip()) > 0, (
                    f"{method_name} docstring should not be empty"
                )

            # Check IBacklinkService methods have docstrings
            for method_name in ["get_backlinks", "extract_internal_links"]:
                method = getattr(IBacklinkService, method_name)
                assert method.__doc__ is not None, (
                    f"{method_name} should have a docstring"
                )
                assert len(method.__doc__.strip()) > 0, (
                    f"{method_name} docstring should not be empty"
                )

        except ImportError:
            pytest.fail("Interfaces should exist")

    def test_interface_inheritance_chain(self):
        """Test that interfaces properly inherit from ABC."""
        try:
            from app.interfaces import IContentProvider, IBacklinkService
            from abc import ABC

            # Check inheritance
            assert ABC in IContentProvider.__mro__, (
                "IContentProvider should inherit from ABC"
            )
            assert ABC in IBacklinkService.__mro__, (
                "IBacklinkService should inherit from ABC"
            )

            # Check that they are recognized as abstract
            assert inspect.isabstract(IContentProvider), (
                "IContentProvider should be abstract"
            )
            assert inspect.isabstract(IBacklinkService), (
                "IBacklinkService should be abstract"
            )

        except ImportError:
            pytest.fail("Interfaces should exist")

    def test_optional_parameters_have_defaults(self):
        """Test that optional parameters have default values."""
        try:
            from app.interfaces import IContentProvider

            # Check get_bookmarks has default for limit
            sig = inspect.signature(IContentProvider.get_bookmarks)
            assert "limit" in sig.parameters
            assert sig.parameters["limit"].default is not inspect.Parameter.empty, (
                "limit parameter should have a default value"
            )

            # Check get_mixed_content has defaults
            sig = inspect.signature(IContentProvider.get_mixed_content)
            assert "page" in sig.parameters
            assert sig.parameters["page"].default is not inspect.Parameter.empty, (
                "page parameter should have a default value"
            )
            assert "per_page" in sig.parameters
            assert sig.parameters["per_page"].default is not inspect.Parameter.empty, (
                "per_page parameter should have a default value"
            )

        except ImportError:
            pytest.fail("IContentProvider interface should exist")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
