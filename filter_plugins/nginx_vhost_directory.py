#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2026, Bodo Schulz <me+ansible@bodsch.me>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

from typing import List

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """ """

    def filters(self):
        return {
            "vhost_directory": self.vhost_directory,
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
