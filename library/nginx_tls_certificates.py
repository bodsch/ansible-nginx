#!/usr/bin/python3
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
        unique_files = []

        if isinstance(self.vhosts, dict):

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

        elif isinstance(self.vhosts, list):

            data = [x for x in self.vhosts if x.get("ssl", {}).get("enabled")]

            cert = [x.get("ssl", {}).get("certificate") for x in data if x.get("ssl", {}).get("enabled")]
            key  = [x.get("ssl", {}).get("certificate_key") for x in data if x.get("ssl", {}).get("enabled")]

            unique_files = list(set(cert + key))

        missing = []
        present = []

        for f in unique_files:
            if not os.path.exists(f):
                missing.append(f)
            else:
                present.append(f)

        vhosts = self.append_tls_state(missing, present)

        result = dict(
            failed = False,
            missing_certs = missing,
            present_certs = present,
            https_vhosts = vhosts
        )

        return result

    def append_tls_state(self, missing = [], present = []):
        """
        """
        data = self.vhosts

        if isinstance(data, dict):
            for k, v in data.items():
                certificate, certificate_key = self._ssl_data(v)

                if certificate and certificate_key:
                    if certificate in missing and certificate_key in missing:
                        data[k]["ssl"]["state"] = "missing"

                    if certificate in present and certificate_key in present:
                        data[k]["ssl"]["state"] = "present"

        elif isinstance(data, list):
            _data = data.copy()
            for d in _data:
                certificate, certificate_key = self._ssl_data(d)

                if certificate and certificate_key:
                    if certificate in missing and certificate_key in missing:
                        d["ssl"]["state"] = "missing"

                    if certificate in present and certificate_key in present:
                        d["ssl"]["state"] = "present"

        return data

    def _ssl_data(self, data):
        """
        """
        ssl = data.get('ssl', {})
        certificate = ssl.get("certificate", None)
        certificate_key = ssl.get("certificate_key", None)

        return certificate, certificate_key

# ===========================================
# Module execution.


def main():

    args = dict(
        vhosts=dict(
            required=True,
            type="raw"
        ),
    )

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True,
    )

    p = NginxTLSCerts(module)
    result = p.run()

    # module.log(msg="= result: {}".format(result))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
