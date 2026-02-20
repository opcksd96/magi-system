import yaml
import toml
import os
import asyncio
from typing import Any


class ConfigManager:
    """Handles YAML/TOML configuration loading and persistence."""

    def __init__(
        self, config_path: str = "config.yaml", models_path: str = "models.toml"
    ):
        self.config_path = config_path
        self.models_path = models_path
        self.settings = {}
        self.models = {}
        self.load_all()

    def load_all(self):
        """Loads all config files from disk with migration support."""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f) or {}

            # Migration: If it's old format (no 'profiles'), wrap it
            if "profiles" not in raw_data:
                print(
                    "DEBUG: [Config] Old format detected. Migrating to Multi-Profile structure..."
                )
                self.settings = {
                    "version": "2.1.0",
                    "active_profile": "default",
                    "profiles": {"default": raw_data},
                }
            else:
                self.settings = raw_data
        else:
            # Default new structure
            self.settings = {
                "version": "2.1.0",
                "active_profile": "default",
                "profiles": {"default": {}},
            }

        if os.path.exists(self.models_path):
            with open(self.models_path, "r", encoding="utf-8") as f:
                self.models = toml.load(f) or {}

    async def save_settings(self):
        """Persists current settings to YAML asynchronously."""
        await asyncio.to_thread(self._sync_save_settings)

    def _sync_save_settings(self):
        """Synchronous helper for saving settings."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.settings, f, allow_unicode=True)

    async def save_models(self):
        """Persists current model data to TOML asynchronously."""
        await asyncio.to_thread(self._sync_save_models)

    def _sync_save_models(self):
        """Synchronous helper for saving models."""
        with open(self.models_path, "w", encoding="utf-8") as f:
            toml.dump(self.models, f)

    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """Helper to get nested settings from the active profile, with global fallback."""
        active_profile = self.settings.get("active_profile", "default")
        profiles = self.settings.get("profiles", {"default": {}})

        keys = key_path.split(".")

        # 1. Try active profile first
        target = profiles.get(active_profile, {})
        found = True
        for k in keys:
            if isinstance(target, dict) and k in target:
                target = target[k]
            else:
                found = False
                break

        if found:
            return target

        # 2. Fallback: Search the original settings root (now under profiles.default or root)
        # Check standard root first
        target = self.settings
        found = True
        for k in keys:
            if isinstance(target, dict) and k in target:
                target = target[k]
            else:
                found = False
                break
        if found:
            return target

        # Check default profile explicitly as last resort
        target = profiles.get("default", {})
        found = True
        for k in keys:
            if isinstance(target, dict) and k in target:
                target = target[k]
            else:
                found = False
                break
        if found:
            return target

        return default
