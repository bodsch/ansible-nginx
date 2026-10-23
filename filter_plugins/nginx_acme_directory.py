#!/usr/bin/python3

# (c) 2021-2026, Bodo Schulz <me+ansible@bodsch.me>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
Ansible filter plugin for .
"""

from __future__ import annotations

import os

from ansible.utils.display import Display

PROTECTED_PATHS = [
    "/",
    "/bin",
    "/boot",
    "/dev",
    "/etc",
    "/home",
    "/lib",
    "/lib64",
    "/media",
    "/mnt",
    "/opt",
    "/proc",
    "/root",
    "/run",
    "/sbin",
    "/srv",
    "/sys",
    "/usr",
    "/var",
]

display = Display()


class FilterModule:

    def filters(self):
        return {
            "is_safe_path": self.is_safe_path,
        }

    def is_safe_path(self, path, protected_paths=None):
        """ """
        display.v(
            f"nginx::is_safe_path(path: {path}, protected_paths: {protected_paths})"
        )

        if not isinstance(path, str) or not path:
            return False

        if not os.path.isabs(path):
            return False

        # Relative Segmente wie ".." normalisieren
        path = os.path.normpath(path)

        if path == "/":
            return False

        protected = protected_paths or PROTECTED_PATHS

        for protected_path in protected:
            protected_path = os.path.normpath(protected_path)

            # Geschützte Verzeichnisse selbst und ihre Eltern blockieren
            if path == protected_path or protected_path.startswith(
                path.rstrip("/") + "/"
            ):
                return False

        return True
