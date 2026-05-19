#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2026, Bodo Schulz <me+ansible@bodsch.me>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
Ansible filter plugin for extracting nginx cache directories.
"""

from __future__ import annotations

from typing import Any

from ansible.utils.display import Display

display = Display()


class FilterModule:
    """
    """

    @staticmethod
    def filters() -> dict[str, Any]:
        return {
            "cache_directory": FilterModule.cache_directory,
        }

    @classmethod
    def cache_directory(
        cls,
        data: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        """
        Extract cache directory paths from nginx cache definitions.

        Input example:
            [
                {
                    "path": "/var/cache/nginx/live",
                    "options": [...]
                }
            ]

        Output example:
            [
                {
                    "path": "/var/cache/nginx/live"
                }
            ]

        Args:
            data:
                List of cache configuration dictionaries.

        Returns:
            List of dictionaries containing only the cache path.
        """
        display.vv(
            f"nginx::cache_directory(data={data})"
        )

        if not isinstance(data, list):
            raise TypeError(
                "cache_directory expects a list of dictionaries."
            )

        result = cls._extract_paths(data)

        display.vv(
            f"nginx::cache_directory(result={result})"
        )

        return result

    @staticmethod
    def _extract_paths(
        data: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        """
        Extract valid path entries from input data.

        Args:
            data:
                Source cache configuration list.

        Returns:
            Normalized path dictionaries.
        """
        return [
            {"path": path}
            for item in data
            if isinstance(item, dict)
            and (path := item.get("path"))
            and isinstance(path, str)
        ]
