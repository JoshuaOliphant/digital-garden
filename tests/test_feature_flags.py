# ABOUTME: Tests for feature flag system to control CSS loading behavior
# ABOUTME: Validates FeatureFlags class can be toggled via environment variables

import os
from unittest.mock import patch


class TestFeatureFlags:
    """Test suite for feature flag functionality."""

    def test_feature_flags_class_exists(self):
        """Test that FeatureFlags class can be imported from config."""
        from app.config import FeatureFlags

        assert FeatureFlags is not None, "FeatureFlags class should exist in app.config"

    def test_feature_flags_has_use_compiled_css_attribute(self):
        """Test that FeatureFlags has USE_COMPILED_CSS attribute."""
        from app.config import FeatureFlags

        flags = FeatureFlags()
        assert hasattr(
            flags, "use_compiled_css"
        ), "FeatureFlags should have use_compiled_css attribute"

    def test_use_compiled_css_defaults_to_false(self):
        """Test that USE_COMPILED_CSS defaults to False when not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove the env var if it exists
            os.environ.pop("USE_COMPILED_CSS", None)

            from app.config import FeatureFlags

            flags = FeatureFlags()

            assert (
                flags.use_compiled_css is False
            ), "use_compiled_css should default to False"

    def test_use_compiled_css_can_be_enabled_via_env(self):
        """Test that USE_COMPILED_CSS can be enabled via environment variable."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("on", True),
        ]

        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"USE_COMPILED_CSS": env_value}):
                from app.config import FeatureFlags

                flags = FeatureFlags()

                assert (
                    flags.use_compiled_css == expected
                ), f"use_compiled_css should be {expected} when USE_COMPILED_CSS={env_value}"

    def test_use_compiled_css_can_be_disabled_via_env(self):
        """Test that USE_COMPILED_CSS can be explicitly disabled via environment variable."""
        test_cases = [
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
            ("off", False),
            ("", False),
        ]

        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"USE_COMPILED_CSS": env_value}):
                from app.config import FeatureFlags

                flags = FeatureFlags()

                assert (
                    flags.use_compiled_css == expected
                ), f"use_compiled_css should be {expected} when USE_COMPILED_CSS={env_value}"

    def test_feature_flags_uses_pydantic_settings(self):
        """Test that FeatureFlags inherits from BaseSettings for proper env handling."""
        from app.config import FeatureFlags
        from pydantic_settings import BaseSettings

        assert issubclass(
            FeatureFlags, BaseSettings
        ), "FeatureFlags should inherit from pydantic_settings.BaseSettings"

    def test_feature_flags_has_proper_config_class(self):
        """Test that FeatureFlags has proper Config class for env variables."""
        from app.config import FeatureFlags

        assert hasattr(
            FeatureFlags, "Config"
        ), "FeatureFlags should have a Config class"

        # Check that it's configured to read from environment
        config = FeatureFlags.Config
        assert hasattr(config, "env_file") or hasattr(
            config, "env_prefix"
        ), "FeatureFlags.Config should be configured for environment variables"

    def test_feature_flags_instance_is_accessible_globally(self):
        """Test that a global feature_flags instance is available."""
        from app.config import feature_flags

        assert feature_flags is not None, "Global feature_flags instance should exist"
        assert hasattr(
            feature_flags, "use_compiled_css"
        ), "Global feature_flags should have use_compiled_css attribute"

    def test_feature_flags_can_be_mocked_for_testing(self):
        """Test that feature flags can be mocked for testing purposes."""
        from app.config import FeatureFlags

        # Test with mocked environment
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            flags = FeatureFlags()
            assert flags.use_compiled_css is True

        # After exiting context, should revert
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "false"}):
            flags = FeatureFlags()
            assert flags.use_compiled_css is False

    def test_feature_flags_validation(self):
        """Test that feature flags properly validate boolean values."""
        from app.config import FeatureFlags

        # Test with invalid boolean values - should handle gracefully
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "invalid"}):
            flags = FeatureFlags()
            # Should either default to False or raise a validation error
            # The behavior depends on implementation
            assert isinstance(
                flags.use_compiled_css, bool
            ), "use_compiled_css should always be a boolean"

    def test_multiple_feature_flags_can_coexist(self):
        """Test that multiple feature flags can be defined and work independently."""
        from app.config import FeatureFlags

        # This test assumes we might add more feature flags in the future
        flags = FeatureFlags()

        # At minimum, we should have use_compiled_css
        assert hasattr(flags, "use_compiled_css")

        # All feature flags should be boolean
        for attr_name in dir(flags):
            if not attr_name.startswith("_") and attr_name not in [
                "Config",
                "model_config",
            ]:
                attr_value = getattr(flags, attr_name, None)
                if attr_value is not None and attr_name.startswith("use_"):
                    assert isinstance(
                        attr_value, bool
                    ), f"Feature flag {attr_name} should be boolean"
