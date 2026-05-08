#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2026, Bodo Schulz <me+ansible@bodsch.me>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

from typing import Dict

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """ """

    def filters(self):
        return {
            "vhost_templates_validate": self.vhost_templates_validate,
        }

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
