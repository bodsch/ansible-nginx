#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2021-2022, Bodo Schulz <bodo@boone-schulz.de>
# Apache (see LICENSE or https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function
import os

from ansible.module_utils.basic import AnsibleModule


class NginxTLSCerts(object):
    """
    """

    def __init__(self, module):
        """
        """
        self.module = module
        self.vhosts = module.params.get("vhosts")

    def run(self):
        """
        """
        cert_files = []

        for vhost, values in self.vhosts.items():
            ssl = values.get("ssl", {})
            if ssl:
                enabled = ssl.get("enabled", True)
                cert = ssl.get("certificate", None)
                key = ssl.get("certificate_key", None)

                if enabled:
                    if cert:
                        cert_files.append(cert)

                    if key:
                        cert_files.append(key)

        unique_files = list(dict.fromkeys(cert_files))

        missing = []
        present = []

        for f in unique_files:
            if not os.path.exists(f):
                missing.append(f)
            else:
                present.append(f)

        result = dict(
            failed = False,
            missing_certs = missing,
            present_certs = present
        )

        return result


# ===========================================
# Module execution.


def main():

    module = AnsibleModule(

        argument_spec=dict(
            vhosts=dict(
                required=True,
                type="dict"
            ),
        ),
        supports_check_mode=True,
    )

    p = NginxTLSCerts(module)
    result = p.run()

    # module.log(msg="= result: {}".format(result))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
