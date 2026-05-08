#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2026, Bodo Schulz <me+ansible@bodsch.me>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

from typing import Any

from ansible.utils.display import Display

display = Display()


class FilterModule(object):

    def filters(self):
        return {
            "upstreams": self.upstreams,
        }

    @classmethod
    def upstreams(
        cls,
        data: list[dict[str, Any]],
        vhost_data: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Build a flat, deduplicated list of nginx upstream definitions.

        Priority:
        - Entries from ``data`` (nginx_upstreams) are taken as-is and are authoritative.
        - Entries from ``vhost_data`` (nginx_vhosts) are added only if their
          ``name`` is not already present in ``data``.
        - Vhost-only entries receive an auto-generated ``description`` indicating
          their origin: "used in {filename}".

        Args:
            data:       Global ``nginx_upstreams`` list (authoritative).
            vhost_data: List of vhost dicts, each with an optional ``upstreams`` key.

        Returns:
            Flat, deduplicated list of upstream dicts.
        """

        display.vv(f"nginx::upstreams(data={data}, vhost_data={vhost_data})")

        result: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        # 1. Seed with global nginx_upstreams – fully authoritative, no modification
        if isinstance(data, list):
            for upstream in data:
                name = upstream.get("name", "")
                if not name or name in seen_names:
                    continue
                seen_names.add(name)
                result.append(dict(upstream))

        # 2. Add vhost-embedded upstreams not already covered by nginx_upstreams
        if isinstance(vhost_data, list):
            for vhost in vhost_data:
                filename = vhost.get("filename", "")
                raw_upstreams: list[dict[str, Any]] = vhost.get("upstreams") or []

                for upstream in raw_upstreams:
                    name = upstream.get("name", "")
                    if not name or name in seen_names:
                        continue

                    seen_names.add(name)

                    entry = dict(upstream)

                    # Annotate origin so consumers know where this upstream came from
                    entry.setdefault(
                        "description",
                        (
                            f"used in {filename}"
                            if filename
                            else f"used in vhost '{vhost.get('name', '?')}'"
                        ),
                    )
                    result.append(entry)

        display.vv(f"nginx::upstreams(result={result})")

        return result
