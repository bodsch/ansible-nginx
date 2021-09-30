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

    def certificates(self, data = None, stats = None):
        """
        """
        result = {}

        display.v(" = data {} ({})".format(json.dumps(data, indent = 2), type(data)))

        #display.v(" -> data  {} ({})".format(data, type(data)))
        #display.v(" -> stats {} ({})".format(stats, type(stats)))

        r = stats.get('results', [])

        display.v("  - {}".format(r))
        for k in r:
            item = k.get('item', {}).get('key','')
            stat = k.get('stat', {})

            #display.v(" --[{}]--------------------------------------------".format(item))
            if stat and not len(stat) == 0:
                data[item]['ssl_certificate_exists'] = True

        display.v(" = data {} ({})".format(json.dumps(data, indent = 2), type(data)))

        return data
