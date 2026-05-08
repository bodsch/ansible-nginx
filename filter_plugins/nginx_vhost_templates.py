#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2026, Bodo Schulz <me+ansible@bodsch.me>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """ """

    def filters(self):
        return {
            "vhost_templates": self.vhost_templates,
        }

    def vhost_templates(self, data, defaults):
        """ """
        display.vv(f"nginx::vhost_templates(data, defaults: {defaults})")
        result = []

        if isinstance(data, list):
            result = [x.get("template") for x in data if x.get("template", None)]

        result += list(defaults.values())

        display.vv(f" = result {result}")
        return result
