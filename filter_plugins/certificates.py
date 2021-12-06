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
            'check_certificates': self.certificates,
        }

    def certificates(self, data=None, stats=None):
        """
          merge two dictionaries
        """
        display.v(" = certificates(data, stats)")
        # display.v("   {}".format(data.get('key', "")))

        r = stats.get('results', [])
        for k in r:
            item = k.get('item', {}).get('key', '')
            ssl = k.get('item', {}).get('value', {}).get('ssl', False)
            lec = k.get('item', {}).get('value', {}).get('letsencrypt', {})

            if lec:
                lec = lec.get("enabled", False)

            if ssl or lec:
                data[item]['ssl_certificate_exists'] = k.get('stat', {}).get('exists', False)

        # display.v(" = data {} -  ({})".format(json.dumps(data, indent=2), type(data)))

        return data
