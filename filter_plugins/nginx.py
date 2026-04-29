#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2026, Bodo Schulz <me+ansible@bodsch.me>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

import hashlib
import os
from typing import Any, Dict, List

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """ """

    def filters(self):
        return {
            "vhost_directory": self.vhost_directory,
            # "vhost_listen": self.vhost_listen,
            "vhost_templates": self.vhost_templates,
            "vhost_templates_checksum": self.vhost_templates_checksum,
            "vhost_templates_validate": self.vhost_templates_validate,
            "http_vhosts": self.http_vhosts,
            # "changed_vhosts": self.changed_vhosts,
            # "certificate_existing": self.certificate_existing,
        }

    def vhost_directory(self, data, directory, state="present"):
        """
        return a list of directories for keyword like 'root_directory', access_log or others
        """
        display.vv(
            f"nginx::vhost_directory(data, directory: {directory}, state: {state})"
        )

        result: List = []

        if isinstance(data, dict):
            for item in data:
                for k, v in item.items():
                    if k == "value":
                        if v.get(directory, None):
                            result.append(v.get(directory))

        elif isinstance(data, list):
            result = [
                x.get(directory)
                for x in data
                if x.get("state", state)
                and x.get(directory, None)
                and x.get("root_directory_create", True)
            ]

        display.vv(f" = result {result}")
        return result

    def vhost_listen(self, data, port, default):
        """
        used in jinja_macros.j2
        """
        display.vv(f"nginx::vhost_listen(data, port: {port}, default: {default})")

        result: List = []

        if isinstance(port, str) or isinstance(port, int):
            result.append(port)

        if isinstance(port, list):
            result = port

        if default:
            result.append("default_server")

        display.vv(f" = result {result}")
        return result

    def vhost_templates(self, data, defaults):
        """ """
        display.vv(f"nginx::vhost_templates(data, defaults: {defaults})")
        result = []

        if isinstance(data, list):
            result = [x.get("template") for x in data if x.get("template", None)]

        result += list(defaults.values())

        display.vv(f" = result {result}")
        return result

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

    def vhost_templates_validate(self, data: Dict, ansible_local: Dict = {}):
        """
        data: {
            'jinja_macros.j2': 'afb7023fe8a33a92d68e283de9eeec87bea5c84fca35af93e9860ddb5422ae34',
            'vhosts/vhost_redirect.conf.j2': 'e6a0114e949fad7cfb2d05a3604b23d0cc761261e11d7d1b84e96225d6701cec',
            'vhosts/vhost_http.conf.j2': '8fef9a3615e415ba032b2fae5b88f3e8de5dd0af0ae4572f33a7b9f0039b06f7',
            'vhosts/vhost_https.conf.j2': '6cea66491de61b1ec01bda78e02ab2cc26ae60d3491e9245234792858743c0a9'
        },
        ansible_local: {
            'jinja_macros.j2': 'afb7023fe8a33a92d68e283de9eeec87bea5c84fca35af93e9860ddb5422ae34',
            'vhosts/vhost_http.conf.j2': '8fef9a3615e415ba032b2fae5b88f3e8de5dd0af0ae4572f33a7b9f0039b06f7',
            'vhosts/vhost_https.conf.j2': '6cea66491de61b1ec01bda78e02ab2cc26ae60d3491e9245234792858743c0a9',
            'vhosts/vhost_redirect.conf.j2': 'e6a0114e949fad7cfb2d05a3604b23d0cc761261e11d7d1b84e96225d6701cec'
        }

        """
        display.vv(
            f"nginx::vhost_templates_validate(data: {data}, ansible_local: {ansible_local})"
        )

        result = {}
        changed_templates = {}

        for tpl, checksum in data.items():
            local_checksum = ansible_local.get(tpl, "-")

            if checksum != local_checksum:
                changed_templates[tpl] = checksum

        changed = len(changed_templates) > 0

        result = {"changed": changed, "templates": changed_templates}

        display.vv(f" = result {result}")
        return result

    def http_vhosts(self, data, tls=False):
        """ """
        display.vv(f"nginx::http_vhosts(data: {data}, tls: {tls})")

        if isinstance(data, dict):
            _data = data.copy()

            for k, v in _data.items():
                ssl = v.get("ssl", {})
                enabled = ssl.get("enabled", False)

                if not tls:
                    if len(ssl) > 0 and enabled:
                        _ = data.pop(k)
                else:
                    if not (len(ssl) > 0 and enabled):
                        _ = data.pop(k)

        if isinstance(data, list):
            if tls:
                data = [x for x in data if x.get("ssl", {}).get("enabled")]
            else:
                data = [x for x in data if not x.get("ssl", {}).get("enabled")]

        display.vv(f" = result {data}")
        return data

    def changed_vhosts(self, data):
        """ """
        display.vv(f"nginx::changed_vhosts(data: {data})")

        result = []

        if isinstance(data, dict):
            """ """
            results = data.get("results", None)
            if results:
                for item in results:
                    changed = item.get("changed", False)
                    if changed:
                        result.append(item.get("item", {}).get("key", None))

        display.vv(f"  => result {result} / changed: {(len(result) > 0)}")
        return len(result) > 0

    def certificate_existing(self, data):
        """
        returns a list of vhosts where the certificate exists.
        """
        display.vv(f"nginx::certificate_existing(data: {data})")

        if isinstance(data, list):
            data = [x for x in data if x.get("ssl", {}).get("state") == "present"]

        display.vv(f" = result {data}")
        return data
