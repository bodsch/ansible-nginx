# python 3 headers, required if submitting to Ansible

# (c) 2021-2022, Bodo Schulz <bodo@boone-schulz.de>
# Apache (see LICENSE or https://opensource.org/licenses/Apache-2.0)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """
        Ansible file jinja2 tests
    """

    def filters(self):
        return {
            'append_certificate_state': self.certificate_state,
        }

    def certificate_state(self, data, state):
        """
        """
        # display.v("certificate_state(data, state)")
        missing = state.get("missing_certs")
        present = state.get("present_certs")

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

        # display.v(f" - {data}")
        return data

    def _ssl_data(self, data):
        """
        """
        ssl = data.get('ssl', {})
        certificate = ssl.get("certificate", None)
        certificate_key = ssl.get("certificate_key", None)

        return certificate, certificate_key
