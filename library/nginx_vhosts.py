#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2024, Bodo Schulz <bodo@boone-schulz.de>
# Apache (see LICENSE or https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function
import os
import shutil
import re
import json

from ansible.module_utils.basic import AnsibleModule
from jinja2 import Environment, FileSystemLoader
from ansible_collections.bodsch.core.plugins.module_utils.directory import create_directory
from ansible_collections.bodsch.core.plugins.module_utils.checksum import Checksum
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results
from ansible_collections.bodsch.core.plugins.module_utils.file import remove_file, create_link


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
        self.acme = module.params.get("acme")

        self.ignore_missing_certificate = module.params.get("ignore_missing_certificate")

        self.default_http_template = template.get("http")
        self.default_https_template = template.get("https")
        self.template_path = template.get("path")

        self.facts_directory = "/etc/ansible/facts.d"
        self.facts_file = os.path.join(self.facts_directory, "nginx.fact")

        self.site_enabled = "/etc/nginx/sites-enabled"
        self.site_available = "/etc/nginx/sites-available"
        self.tmp_directory = os.path.join("/run/.ansible", f"nginx_vhosts.{str(os.getpid())}")

    def run(self):
        """
        """
        nginx_facts = dict()
        self.nginx_version = "0.0.0"

        self.checksum = Checksum(self.module)

        create_directory(directory=self.tmp_directory, mode="0750")

        result_state = []

        # read facts
        if os.path.exists(self.facts_file):
            rc, out, err = self._exec([self.facts_file])

            nginx_facts = out

        if len(nginx_facts) > 0:
            if isinstance(nginx_facts, str):
                nginx_facts = json.loads(nginx_facts)

                self.nginx_version = nginx_facts.get("version", "0.0.0")

        if isinstance(self.vhosts, list):
            for vhost in self.vhosts:
                res = {}
                state = vhost.get("state", "present")
                # enabled = vhost.get("enabled", True)
                name = vhost.get("name", None)
                # self.module.log(msg=f" - vhost {vhost}")
                # self.module.log(msg=f"   name {name}")

                res[name] = dict()

                if state == "absent":
                    disabled, removed = self.remove_vhost(vhost)
                    msg = ""
                    changed = False
                    if disabled:
                        changed = True
                        msg = "The VHost was successfuly disabled."
                    elif removed:
                        changed = True
                        msg = "The VHost was successfuly removed."
                    elif disabled and removed:
                        changed = True
                        msg = "The VHost was successfuly disabled and removed."

                    if changed:
                        res[name].update({
                            "changed": changed,
                            "msg": msg
                        })

                        result_state.append(res)

                else:
                    failed, changed, msg = self.create_vhost(vhost)

                    res[name].update({
                        "failed": failed,
                        "changed": changed,
                        "msg": msg
                    })

                    result_state.append(res)

        # define changed for the running tasks
        _state, _changed, _failed, state, changed, failed = results(self.module, result_state)

        result = dict(
            changed=_changed,
            failed=_failed,
            msg=result_state
        )

        shutil.rmtree(self.tmp_directory)

        return result

    def create_vhost(self, data):
        """
        """
        # self.module.log(msg="create_vhost(data)")

        # state = data.get("state", "present")
        enabled = data.get("enabled", True)
        template_file = data.get("template", None)
        tls = data.get("ssl", None)
        tls_enabled = False

        if tls:
            tls_enabled = tls.get("enabled", False)
            tls_cert_state = tls.get("state", "missing")

            if tls_enabled and tls_cert_state == "missing":

                if self.ignore_missing_certificate:
                    return False, False, "[WARNING] TLS certificate missing"
                else:
                    return True, False, "[ERROR] TLS certificate missing"

        if not template_file:
            if tls_enabled:
                template_file = self.default_https_template
            else:
                template_file = self.default_http_template

        template = os.path.join(self.template_path, template_file)
        # self.module.log(msg=f"- template {template}")

        if not os.path.exists(template):
            """
            """
            _error = True
            _changed = False
            _msg = f"The template {template_file} does not exist."
            return _error, _changed, _msg

        file_available, file_enabled, file_temporary = self.__file_names(data)

        # self.module.log(msg=f"- file_available {file_available} - {file_enabled} - {file_temporary}")

        vhost_data = self.render_template(template, data)

        changed, msg = self.save_vhost(file_available, file_temporary, vhost_data)

        if enabled:
            enabled = self.enable_vhost(file_available, file_enabled)
            if enabled:
                if changed:
                    msg += " and enabled."
                else:
                    changed = True
                    msg = "The VHost was successfully enabled."
        else:
            disabled = self.disable_vhost(file_enabled)
            if disabled:
                if changed:
                    msg += " and disabled."
                else:
                    changed = True
                    msg = "The VHost was successfuly disabled."

        return False, changed, msg

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

            # self.module.log(msg=f"'{value}' is {result}")

            return result

        def regex_replace(s, find, replace):
            """
                A non-optimal implementation of a regex filter
            """
            # self.module.log(msg=f"regex_replace('{s}', '{find}', '{replace}')")
            result = re.sub(find, replace, s).strip()
            # self.module.log(msg=f"='{result}'")
            return result

        def split(value, s=''):
            if isinstance(value, str):
                # ignore empty strings
                return list(filter(None, value.split(s)))
                # return value.split(s)

        def validate_listener(data, regex='(quic|reuseport)', replace=""):
            """
            """
            result = []
            # self.module.log(msg=f"validate_listener({data}, {regex}, {replace})")

            if isinstance(data, str):
                result.append(re.sub(regex, replace, data).strip())
            elif isinstance(data, list):
                for i in data:
                    result.append(re.sub(regex, replace, str(i)).strip())

            # self.module.log(msg=f"='{result}'")
            return result

        def version_compare(value, version, compare_operator='eq'):
            ''' Perform a version comparison on a value '''
            import operator
            from packaging.version import Version
            # from ansible import errors
            from ansible.module_utils.common.text.converters import to_native, to_text

            op_map = {
                '==': 'eq', '=': 'eq', 'eq': 'eq',
                '<': 'lt', 'lt': 'lt',
                '<=': 'le', 'le': 'le',
                '>': 'gt', 'gt': 'gt',
                '>=': 'ge', 'ge': 'ge',
                '!=': 'ne', '<>': 'ne', 'ne': 'ne'
            }

            if not value:
                raise ("Input version value cannot be empty")

            if not version:
                raise ("Version parameter to compare against cannot be empty")

            if compare_operator in op_map:
                compare_operator = op_map[compare_operator]
            else:
                valid_compare = ", ".join(map(repr, op_map))

                raise (
                    f'Invalid operator type ({compare_operator}). Must be one of {valid_compare}')

            try:
                method = getattr(operator, compare_operator)
                return method(Version(to_text(value)), Version(to_text(version)))

            except Exception as e:
                raise (f'Version comparison failed: {to_native(e)}')

        if os.path.isfile(vhost_template):
            file_path = os.path.os.path.dirname(os.path.realpath(vhost_template))
            file_name = os.path.basename(os.path.realpath(vhost_template))

            # Create the jinja2 environment.
            # Notice the use of trim_blocks, which greatly helps control whitespace.
            jinja_environment = Environment(loader=FileSystemLoader(file_path), trim_blocks=True, lstrip_blocks=True)

            jinja_environment.filters.update({
                'bodsch.core.var_type': var_type,
                'bodsch.core.type': var_type,
                'split': split,
                'regex_replace': regex_replace,
                'validate_listener': validate_listener,
                'version_compare': version_compare,
            })

            output = jinja_environment.get_template(file_name).render(
                item=data,
                nginx_acme=self.acme,
                nginx_version=self.nginx_version)

        return output

    def remove_vhost(self, data):
        """
        """
        self.module.log(msg=f"remove_vhost({data})")
        disabled = False
        removed = False

        file_available, file_enabled, _ = self.__file_names(data)

        if os.path.islink(file_available) and os.readlink(file_available) == file_enabled:
            disabled = remove_file(file_available)

        if os.path.isfile(file_enabled):
            removed = remove_file(file_enabled)

        return disabled, removed

    def save_vhost(self, file_name, file_temporary, data):
        """
        """
        with open(file_temporary, "w") as f:
            f.write(data)

        old_checksum = self.checksum.checksum_from_file(file_name)
        new_checksum = self.checksum.checksum_from_file(file_temporary)

        changed = not (new_checksum == old_checksum)
        new_file = False
        msg = "The VHost has not been changed"

        # self.module.log(msg=f"   file_name {file_name}")
        # self.module.log(msg=f"   file_temporary {file_temporary}")
        # self.module.log(msg=f"   old_checksum {old_checksum}")
        # self.module.log(msg=f"   new_checksum {new_checksum}")
        # self.module.log(msg=f"   changed {changed}")

        if changed:
            new_file = (old_checksum is None)
            shutil.move(file_temporary, file_name)
            msg = "The VHost was successfully changed"

        if new_file:
            msg = "The VHost was successfully created"

        return changed, msg

    def enable_vhost(self, file_available, file_enabled):
        """
        """
        # self.module.log(msg=f"enable_vhost({file_available}, {file_enabled})")
        changed = False

        if os.path.islink(file_enabled) and os.readlink(file_enabled) == file_available:
            # link exists and is valid
            pass
        else:
            if not os.path.islink(file_enabled):
                create_link(file_available, file_enabled)
            else:
                if os.readlink(file_enabled) != file_available:
                    self.module.log(msg=f"path '{file_enabled}' is a broken symlink")
                    create_link(file_available, file_enabled, True)
                else:
                    create_link(file_available, file_enabled)

            changed = True

        return changed

    def disable_vhost(self, file_enabled):
        """
        """
        # self.module.log(msg=f"disable_vhost({file_enabled})")

        changed = False

        changed = remove_file(file_enabled)

        return changed

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

        # self.module.log(msg=f"   enabled {enabled}")
        # self.module.log(msg=f"   available {available}")
        # self.module.log(msg=f"   temporary {temporary}")

        return available, enabled, temporary

    def _exec(self, cmd, check=False):
        """
          execute shell commands
        """
        rc, out, err = self.module.run_command(cmd, check_rc=check)

        if rc != 0:
            self.module.log(msg=f"  rc : '{rc}'")
            self.module.log(msg=f"  out: '{out}'")
            self.module.log(msg=f"  err: '{err}'")

        return (rc, out, err)

# ===========================================
# Module execution.


def main():

    args = dict(
        vhosts=dict(
            required=True,
            type="list"
        ),
        template=dict(
            required=True,
            type="dict"
        ),
        dest=dict(
            required=False,
            default="/etc/nginx/sites-available"
        ),
        acme=dict(
            required=False,
            type=dict
        ),
        ignore_missing_certificate=dict(
            required=False,
            type=bool,
            default=False
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
