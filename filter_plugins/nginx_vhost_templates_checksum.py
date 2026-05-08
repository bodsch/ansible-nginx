#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2026, Bodo Schulz <me+ansible@bodsch.me>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

import hashlib
import os
from typing import Any

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """ """

    def filters(self):
        return {
            "vhost_templates_checksum": self.vhost_templates_checksum,
        }

    def vhost_templates_checksum(self, data: list[str]) -> dict[str, Any]:
        """
        Compute SHA-256 checksums for a list of template file paths and
        determine the longest common directory prefix shared by all paths.

        Args:
            data: List of absolute template file paths on the Ansible controller.

        Returns:
            A dict with two keys:

            ``base_path``
                The longest common directory prefix of all existing paths,
                e.g. ``"/home/bodsch/.../templates"``.
                Empty string when no files exist.

            ``checksums``
                Dict mapping each existing file path *relative to* ``base_path``
                to its SHA-256 hex digest.

        Example return value::

            {
                "base_path": "/home/bodsch/src/ansible/ansible-nginx/templates",
                "checksums": {
                    "jinja_macros.j2":              "afb702...",
                    "vhosts/vhost_redirect.conf.j2": "e6a011...",
                    "vhosts/vhost_http.conf.j2":     "8fef9a...",
                    "vhosts/vhost_https.conf.j2":    "6cea66...",
                }
            }
        """
        display.vv(f"nginx::vhost_templates_checksum(data: {data})")

        abs_checksums: dict[str, str] = {}

        for tpl in data:
            if os.path.exists(tpl):
                with open(tpl, "rb") as fh:
                    file_bytes = fh.read()
                    abs_checksums[tpl] = hashlib.sha256(file_bytes).hexdigest()

        if abs_checksums:
            dirs = [os.path.dirname(p) for p in abs_checksums]
            base_path = os.path.commonpath(dirs)
            # Strip base_path from every key; os.path.relpath handles the
            # path arithmetic cleanly without manual string slicing.
            checksums = {
                os.path.relpath(p, base_path): digest
                for p, digest in abs_checksums.items()
            }
        else:
            base_path = ""
            checksums = {}

        result = dict(base_path=base_path, checksums=checksums)

        display.vv(f" = result {result}")
        return result
