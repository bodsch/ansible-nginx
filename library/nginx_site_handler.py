#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2021-2022, Bodo Schulz <bodo@boone-schulz.de>
# Apache (see LICENSE or https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function
import os

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results
from ansible_collections.bodsch.core.plugins.module_utils.file import remove_file, create_link


class NginxSiteHandler(object):
    """
    """

    def __init__(self, module):
        """
        """
        self.module = module
        self.state  = module.params.get("state")
        self.enabled = module.params.get("enabled")
        self.vhosts = module.params.get("vhosts")

        self.site_enabled = "/etc/nginx/sites-enabled"
        self.site_available = "/etc/nginx/sites-available"

    def run(self):
        """
        """
        result_state = []

        if isinstance(self.vhosts, dict):
            for vhost, values in self.vhosts.items():
                file_name = values.get("filename", None)
                enabled = values.get("enabled", True)
                state = values.get("state", "present")

                # self.module.log(msg=f" - {vhost} : (state: {state} / {self.state}) / (enabled: {enabled} / {self.enabled}) ")

                if not file_name:
                    file_name = f"{vhost}.conf"

                # self.module.log(msg=f"   - {file_name}")

                if not self.enabled and not enabled:
                    changed = self.disable_site(file_name)

                    if changed:
                        res = {}
                        res[vhost] = dict(
                            state = f"vhost {vhost} successfuly disabled"
                        )
                        result_state.append(res)

                if self.enabled and enabled:
                    changed = self.enable_site(file_name)

                    if changed:
                        res = {}
                        res[vhost] = dict(
                            state = f"vhost {vhost} successfuly enabled"
                        )
                        result_state.append(res)

                if self.state == "absent" and state == "absent":
                    changed = self.remove_site(file_name)

                    if changed:
                        res = {}
                        res[vhost] = dict(
                            state = f"vhost {vhost} successfuly disabled and removed"
                        )
                        result_state.append(res)

        elif isinstance(self.vhosts, list):
            for vhost in self.vhosts:
                name = vhost.get("name", None)
                file_name = vhost.get("filename", None)
                enabled = vhost.get("enabled", True)
                state = vhost.get("state", "present")

                if not file_name:
                    file_name = f"{name}.conf"

                if not self.enabled and not enabled:
                    changed = self.disable_site(file_name)

                    if changed:
                        res = {}
                        res[name] = dict(
                            state = f"vhost {name} successfuly disabled"
                        )
                        result_state.append(res)

                if self.enabled and enabled:
                    changed = self.enable_site(file_name)

                    if changed:
                        res = {}
                        res[name] = dict(
                            state = f"vhost {name} successfuly enabled"
                        )
                        result_state.append(res)

                if self.state == "absent" and state == "absent":
                    changed = self.remove_site(file_name)

                    if changed:
                        res = {}
                        res[name] = dict(
                            state = f"vhost {name} successfuly disabled and removed"
                        )
                        result_state.append(res)

        # define changed for the running tasks
        _state, _changed, _failed, state, changed, failed = results(self.module, result_state)

        result = dict(
            changed = _changed,
            failed = False,
            state = result_state
        )

        return result

    def disable_site(self, file_name):
        """
        """
        changed = False

        site_file = os.path.join(self.site_enabled, file_name)

        changed = remove_file(site_file)

        return changed

    def enable_site(self, file_name):
        """
        """
        changed = False

        source = os.path.join(self.site_available, file_name)
        destination = os.path.join(self.site_enabled, file_name)

        if os.path.islink(destination) and os.readlink(destination) == source:
            # link exists and is valid
            pass
        else:
            if not os.path.islink(destination):
                create_link(source, destination)
            else:
                if os.readlink(destination) != source:
                    self.module.log(msg=f"path '{destination}' is a broken symlink")
                    create_link(source, destination, True)
                else:
                    create_link(source, destination)

            changed = True

        return changed

    def remove_site(self, file_name):
        """
        """
        changed = False

        self.disable_site(file_name)

        source = os.path.join(self.site_available, file_name)

        changed = remove_file(source)

        return changed


# ===========================================
# Module execution.


def main():

    args = dict(
        state = dict(
            required = False,
            default = "present",
            choices = [
                "absent",
                "present"
            ]
        ),
        enabled = dict(
            required = False,
            type="bool"
        ),
        vhosts=dict(
            required=True,
            type="raw"
        ),
        site_path = dict(
            required = False,
            default = ""
        ),
    )

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True,
    )

    p = NginxSiteHandler(module)
    result = p.run()

    # module.log(msg="= result: {}".format(result))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
