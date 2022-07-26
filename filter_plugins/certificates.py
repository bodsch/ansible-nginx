# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.utils.display import Display

import json
import crypt

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
        display.v(" = certificates(data, state)")

        missing = state.get("missing_certs")
        present = state.get("present_certs")

        for k, v in data.items():
            ssl = v.get('ssl', {})
            enabled = ssl.get("enabled", False)
            certificate = ssl.get("certificate", None)
            certificate_key = ssl.get("certificate_key", None)

            if certificate and certificate_key:
                if certificate in missing and certificate_key in missing:
                    data[k]["ssl"]["state"] = "missing"

                if certificate in present and certificate_key in present:
                    data[k]["ssl"]["state"] = "present"

        return data
