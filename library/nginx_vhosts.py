#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2021-2022, Bodo Schulz <bodo@boone-schulz.de>
# Apache (see LICENSE or https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function
import os
import shutil
import re

from ansible.module_utils.basic import AnsibleModule
from jinja2 import Template, Environment, FileSystemLoader
from ansible_collections.bodsch.core.plugins.module_utils.directory import create_directory
from ansible_collections.bodsch.core.plugins.module_utils.checksum import Checksum
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results

class NginxVHosts(object):
    """
    """

    def __init__(self, module):
        """
        """
        self.module = module
        self.vhosts = module.params.get("vhosts")
        self.dest = module.params.get("dest")

        template = module.params.get("template")
        self.default_http_template = template.get("http")
        self.default_https_template = template.get("https")
        self.template_path = template.get("path")
        self.acme = template.get("acme")

        self.site_enabled = "/etc/nginx/sites-enabled"
        self.site_available = "/etc/nginx/sites-available"
        self.tmp_directory = os.path.join("/run/.ansible", f"nginx_vhosts.{str(os.getpid())}")

    def run(self):
        """
        """
        self.checksum = Checksum(self.module)

        create_directory(directory=self.tmp_directory, mode="0750")

        result_state = []

        if isinstance(self.vhosts, list):
            for vhost in self.vhosts:
                state = vhost.get("state", "present")
                enabled = vhost.get("enabled", True)

                self.module.log(msg=f" - vhost {vhost}")
                self.module.log(msg=f"   state {state}")
                self.module.log(msg=f"   enabled {enabled}")

                if state == "absent":
                    disabled, removed = self.remove_vhost(vhost)
                else:
                    result = self.create_vhost(vhost)

                    if not enabled:
                        disabled = self.disable_vhost(vhost)

        # define changed for the running tasks
        _state, _changed, _failed, state, changed, failed = results(self.module, result_state)

        result = dict(
            changed = _changed,
            failed = False,
            msg = result_state
        )

        # shutil.rmtree(self.tmp_directory)

        return result

    def create_vhost(self, data):
        """
        """
        state = data.get("state", "present")
        enabled = data.get("enabled", True)
        template = data.get("template", None)
        tls = data.get("ssl", None)
        template = data.get("template", None)
        tls = data.get("ssl", None)

        if tls:
            tls = tls.get("enabled", False)

        if not template:
            if tls:
                template = self.default_https_template
            else:
                template = self.default_http_template

        template = os.path.join(self.template_path, template)

        self.module.log(msg=f"   template {template}")

        file_available, _, file_temporary = self.__file_names(data)

        vhost_data = self.render_template(template, data)

        self.save_vhost(file_available, file_temporary, vhost_data)

        if enabled:
            self.enable_vhost(data)


    def render_template(self, vhost_template, data):
        """
        """
        output = None

        # Custom filter method
        def var_type(value):
            result = None
            if isinstance(value, list):
                result = "list"
            elif isinstance(value, dict):
                result = "dict"
            elif isinstance(value, str):
                result = "string"
            elif isinstance(value, int):
                result = "int"
            elif isinstance(value, bool):
                result = "boolean"
            else:
                result = None

            self.module.log(msg=f"'{value}' is {result}")

            return result

        def regex_replace(s, find, replace):
            """
                A non-optimal implementation of a regex filter
            """
            self.module.log(msg=f"regex_replace('{s}', '{find}', '{replace}')")

            result = re.sub(find, replace, s).strip()
            self.module.log(msg=f"='{result}'")
            return result

        def is_list(value):
            return isinstance(value, list)

        def is_dict(value):
            return isinstance(value, dict)

        if os.path.isfile(vhost_template):

            file_path = os.path.os.path.dirname(os.path.realpath(vhost_template))
            file_name = os.path.basename(os.path.realpath(vhost_template))

            # Create the jinja2 environment.
            # Notice the use of trim_blocks, which greatly helps control whitespace.
            jinja_environment = Environment(loader=FileSystemLoader(file_path), trim_blocks=True, lstrip_blocks=True)

            jinja_environment.filters.update({
                'bodsch.core.var_type': var_type,
                'is_list': is_list,
                'is_dict': is_dict,
                'regex_replace': regex_replace
            })

            # jinja_environment.filters['regex_replace'] = regex_replace

            output = jinja_environment.get_template(file_name).render(item=data, nginx_acme=self.acme)

            # self.module.log(output)

        return output


    def remove_vhost(self, data):
        """
        """
        disabled = False
        removed = False

        name = data.get("name")
        file_name = data.get("filename", None)

        if not file_name:
            file_name = f"{name}.conf"

        enabled = os.path.join(self.site_enabled, file_name)
        available = os.path.join(self.site_available, file_name)

        if os.path.islink(available) and os.readlink(available) == enabled:
            disabled = remove_file(available)

        if os.path.isfile(enabled):
            removed = remove_file(enabled)

        return disabled, removed


    def save_vhost(self, file_name, file_temporary, data):
        """
        """
        # data_file    = os.path.join(file_name)
        # tmp_file     = os.path.join(self.tmp_directory, file_name)

        with open(file_temporary, "w") as f:
            f.write(data)

        old_checksum = self.checksum.checksum_from_file(file_name)
        new_checksum = self.checksum.checksum_from_file(file_temporary)

        changed = not (new_checksum == old_checksum)

        self.module.log(msg=f"   file_name {file_name}")
        self.module.log(msg=f"   file_temporary {file_temporary}")
        self.module.log(msg=f"   old_checksum {old_checksum}")
        self.module.log(msg=f"   new_checksum {new_checksum}")
        self.module.log(msg=f"   changed {changed}")

        if changed:
            shutil.move(file_temporary, file_name)

        return changed

    def enable_vhost(self, data):
        return None

    def disable_vhost(self, data):
        return None

    def __file_names(self, data):
        """
        """
        name = data.get("name")
        file_name = data.get("filename", None)

        if not file_name:
            file_name = f"{name}.conf"

        enabled = os.path.join(self.site_enabled, file_name)
        available = os.path.join(self.site_available, file_name)
        temporary = os.path.join(self.tmp_directory, file_name)

        self.module.log(msg=f"   enabled {enabled}")
        self.module.log(msg=f"   available {available}")
        self.module.log(msg=f"   temporary {temporary}")

        return available, enabled, temporary



# ===========================================
# Module execution.


def main():

    args = dict(
        vhosts=dict(
            required=True,
            type="list"
        ),
        template = dict(
            required=True,
            type="dict"
        ),
        dest = dict(
            required=False,
            default = "/etc/nginx/sites-available"
        ),
        acme = dict(
            required=False,
            type = dict
        ),
    )

    module = AnsibleModule(

        argument_spec=args,
        supports_check_mode=True,
    )

    p = NginxVHosts(module)
    result = p.run()

    module.log(msg="= result: {}".format(result))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
