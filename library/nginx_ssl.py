#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2022, Bodo Schulz <bodo@boone-schulz.de>
# Apache (see LICENSE or https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function
import os
import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results
from ansible_collections.bodsch.core.plugins.module_utils.directory import create_directory
from ansible_collections.bodsch.core.plugins.module_utils.checksum import Checksum

TPL_SSL = """# generated by ansible

{% for key, value in item.items() %}
    {% if key == "ssl_protocols" %}
{{ key.ljust(24) }}  {{ value | join(' ') }};
    {% elif (value is sameas true or value is sameas false) %}
{{ key.ljust(24) }}  {{ 'on' if value else 'off' }};
    {% else %}
{{ key.ljust(24) }}  {{ value }};
    {% endif %}
{% endfor %}

"""

TPL_CIPHERS = """# generated by ansible

ssl_ciphers  {{ item }};

"""


class NginxSsl(object):
    """
    """

    def __init__(self, module):
        """
        """
        self.module = module
        self.ssl_config = module.params.get("config")
        self.dest = module.params.get("dest")
        self.cache_directory = "/var/cache/ansible/nginx"

    def run(self):
        """
        """
        result_state = []

        self.checksum = Checksum(self.module)

        create_directory(self.cache_directory)
        checksum_file = os.path.join(self.cache_directory, "ssl_config")

        changed, checksum, old_checksum = self.checksum.validate(
            checksum_file=checksum_file,
            data=self.ssl_config
        )

        if not changed:
            return dict(
                changed = False,
                msg = "The ssl configuration has not been changed."
            )

        if isinstance(self.ssl_config, dict):

            ssl_config = self.ssl_config.copy()
            # remove our 'enabled' value
            _ = ssl_config.pop("enabled")

            ssl_ciphers = ssl_config.get("ssl_ciphers", {})
            _ = ssl_config.pop("ssl_ciphers")

            file_name = "ssl.conf"

            _failed, _changed, _msg = self._write_template(
                "ssl",
                os.path.join(self.dest, file_name),
                ssl_config
            )

            res = {}
            res[file_name] = dict(
                failed=_failed,
                changed=_changed,
                msg=_msg
            )
            result_state.append(res)

            for key, values in ssl_ciphers.items():
                res = {}
                file_name = f"ssl_{key}.conf"
                _failed, _changed, _msg = self._write_template(
                    "ssl_ciphers",
                    os.path.join(self.dest, file_name),
                    values
                )

                res[file_name] = dict(
                    failed=_failed,
                    changed=_changed,
                    msg=_msg
                )

                result_state.append(res)

        # define changed for the running tasks
        _state, _changed, _failed, state, changed, failed = results(self.module, result_state)

        result = dict(
            changed = _changed,
            failed = _failed,
            result = result_state
        )

        return result

    def _write_template(self, type, file_name, data):
        """
        """
        if isinstance(data, dict):
            """
                sort data
            """
            data = json.dumps(data, sort_keys=True)
            if isinstance(data, str):
                data = json.loads(data)

        if isinstance(data, list):
            data = ":".join(data)

        checksum_file = os.path.join(self.cache_directory, f"{os.path.basename(file_name)}.checksum")

        changed, checksum, old_checksum = self.checksum.validate(
            checksum_file=checksum_file,
            data=data
        )

        if not changed:
            return False, False, "The configuration file has not been changed."

        from jinja2 import Template

        if type == "ssl":
            tpl = TPL_SSL
        else:
            tpl = TPL_CIPHERS

        tm = Template(tpl, trim_blocks=True, lstrip_blocks = True)
        d = tm.render(item=data)

        with open(file_name, "w") as f:
            f.write(d)

        self.checksum.write_checksum(
            checksum_file=checksum_file,
            checksum=checksum
        )

        return False, True, "The configuration file was written successfully."


# ===========================================
# Module execution.


def main():

    args = dict(
        config=dict(
            required=True,
            type="dict"
        ),
        dest = dict(
            required=False,
            default = "/etc/nginx/includes.d"
        )
    )

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True,
    )

    p = NginxSsl(module)
    result = p.run()

    # module.log(msg="= result: {}".format(result))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
