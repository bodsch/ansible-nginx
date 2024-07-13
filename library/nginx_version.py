#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2024, Bodo Schulz <bodo@boone-schulz.de>
# Apache (see LICENSE or https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function
import re

from ansible.module_utils.basic import AnsibleModule


class NginxVersion(object):
    """
    """

    def __init__(self, module):
        """
        """
        self.module = module

        self.nginx_bin = module.get_bin_path('nginx', True)

    def run(self):
        """
        """
        version = "0.0.0"

        args_list = [
            self.nginx_bin,
            "-v"
        ]

        rc, out, err = self.__exec(args_list)

        pattern = re.compile(r".*nginx/(?P<version>[0-9.]+).*", flags=re.MULTILINE | re.DOTALL)
        re_result = re.search(pattern, err.strip())

        if re_result:
            version = re_result.group("version")

        result = dict(
            changed=False,
            failed=False,
            rc=rc,
            version=version
        )

        return result

    def __exec(self, commands, check_rc=True):
        """
        """
        rc, out, err = self.module.run_command(
            commands,
            check_rc=check_rc)

        self.module.log(msg=f"cmd: '{commands}'")
        self.module.log(msg=f"  rc : '{rc}'")
        self.module.log(msg=f"  out: '{out}'")
        self.module.log(msg=f"  err: '{err}'")
        for line in err.splitlines():
            self.module.log(msg=f"   {line}")

        return rc, out, err


# ===========================================
# Module execution.


def main():

    args = dict()

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True,
    )

    p = NginxVersion(module)
    result = p.run()

    module.log(msg="= result: {}".format(result))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
