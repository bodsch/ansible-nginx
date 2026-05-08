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
            "http_vhosts": self.http_vhosts,
        }

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
