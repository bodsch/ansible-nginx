# python 3 headers, required if submitting to Ansible

# (c) 2021-2022, Bodo Schulz <bodo@boone-schulz.de>
# Apache (see LICENSE or https://opensource.org/licenses/Apache-2.0)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
# import json
import hashlib

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """
        Ansible file jinja2 tests
    """

    def filters(self):
        return {
            'vhost_directory': self.vhost_directory,
            'vhost_listen': self.vhost_listen,
            'vhost_templates': self.vhost_templates,
            'vhost_templates_checksum': self.vhost_templates_checksum,
            'vhost_templates_validate': self.vhost_templates_validate,
            'http_vhosts': self.http_vhosts,
            'changed_vhosts': self.changed_vhosts,
            'certificate_existing': self.certificate_existing,
        }

    def vhost_directory(self, data, directory, state="present"):
        """
          return a list of directories for keyword like 'root_directory', access_log or others
        """
        # display.v(f"vhost_directory(data, {directory}, {state})")
        result = []

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
                if x.get("state", state) and x.get(directory, None) and x.get("root_directory_create", True)
            ]

        # display.v(f" = result {result}")
        return result

    def vhost_listen(self, data, port, default):
        """
            used in jinja_macros.j2
        """
        # display.v(f"vhost_listen({port}, {default})")
        result = []

        if (isinstance(port, str) or isinstance(port, int)):
            result.append(port)

        if isinstance(port, list):
            result = port

        if default:
            result.append('default_server')

        # display.v(f" = result {result}")
        return result

    def vhost_templates(self, data, defaults):
        """
        """
        display.v(f"vhost_templates(data, {defaults})")
        result = []

        if isinstance(data, list):
            result = [
                x.get("template")
                for x in data
                if x.get("template", None)
            ]

        result += list(defaults.values())

        display.v(f" = result {result}")
        return result

    def vhost_templates_checksum(self, data):
        """
        """
        result = {}

        for tpl in data:
            if os.path.exists(tpl):
                with open(tpl, "rb") as f:
                    bytes = f.read()
                    readable_hash = hashlib.sha256(bytes).hexdigest()
                    result[tpl] = readable_hash

        # display.v(f" = result {result}")
        return result

    def vhost_templates_validate(self, data, ansible_local):
        """
        """
        result = {}
        changed_templates = {}

        for tpl, checksum in data.items():
            local_checksum = ansible_local.get(tpl, "-")

            if checksum != local_checksum:
                changed_templates[tpl] = checksum

        changed = len(changed_templates) > 0

        result = {
            "changed": changed,
            "templates": changed_templates
        }

        # display.v(f" = result {result}")
        return result

    def http_vhosts(self, data, tls=False):
        """
        """
        # display.v(f"http_vhosts(data, {tls})")

        if isinstance(data, dict):
            _data = data.copy()

            for k, v in _data.items():
                ssl = v.get('ssl', {})
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

        # display.v(f" = result {data}")
        return data

    def changed_vhosts(self, data):
        """
        """
        result = []

        if isinstance(data, dict):
            """
            """
            results = data.get("results", None)
            if results:
                for item in results:
                    changed = item.get("changed", False)
                    if changed:
                        result.append(item.get("item", {}).get("key", None))

        # display.v(f"  => changed: {(len(result) > 0)} - {result}")
        return (len(result) > 0)

    def certificate_existing(self, data):
        """
            returns a list of vhosts where the certificate exists.
        """
        # display.v(f"certificate_existing({data})")
        if isinstance(data, list):
            data = [x for x in data if x.get("ssl", {}).get("state") == "present"]

        # display.v(f" = result {data}")
        return data
