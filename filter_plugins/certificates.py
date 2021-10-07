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
            'active_vhost': self.active_vhost,
            'letsencrypt': self.letsencrypt,
            'create_vhost': self.create_vhost,
        }

    def certificates(self, data=None, stats=None):
        """
        """
        r = stats.get('results', [])
        for k in r:
            item = k.get('item', {}).get('key', '')
            ssl = k.get('item', {}).get('value', {}).get('ssl', False)
            lec = k.get('item', {}).get('value', {}).get('letsencrypt', False)

            if ssl or lec:
                data[item]['ssl_certificate_exists'] = k.get('stat', {}).get('exists', False)

        return data

    def active_vhost(self, data=None, certificate_exists=False):
        """
        """
        display.v(" = data {} ({})".format(json.dumps(data, indent=2), type(data)))

        result = False
        enabled = True
        present = True

        value = data.get('value', {})

        ssl = value.get("ssl", False)
        letsencrypt = value.get("letsencrypt", False)

        display.v(" -> enabled            {} ({})".format(enabled, type(enabled)))
        display.v(" -> present            {} ({})".format(present, type(present)))
        display.v(" -> ssl                {} ({})".format(ssl, type(ssl)))
        display.v(" -> letsencrypt        {} ({})".format(letsencrypt, type(letsencrypt)))
        display.v(" -> certificate_exists {} ({})".format(certificate_exists, type(certificate_exists)))

        if enabled and present:
            result = True

            if not ssl and certificate_exists:
                result = False

            if letsencrypt:
                result = False

        display.v(" = result {}".format(result))

        return result

    def letsencrypt(self, data):
        """
        """
        display.v(" = data {} ({})".format(json.dumps(data, indent=2), type(data)))

        result = {}

        for k, v in data.items():
            display.v(" = data {} ({})".format(json.dumps(v, indent=2), type(v)))
            if v.get('letsencrypt', False):
                result[k] = dict(
                    domains=v.get('domains', []),
                    email=v.get('letsencrypt_email', '')
                )

        return result

    def create_vhost(self, data, mode='http'):
        """
        """
        display.v(" = data {} ({})".format(json.dumps(data, indent=2), type(data)))

        result = False
        present = True

        value = data.get('value', {})

        state = value.get("state", True)
        ssl = value.get("ssl", False)
        letsencrypt = value.get("letsencrypt", False)

        display.v(" -> present            {} ({})".format(present, type(present)))
        display.v(" -> ssl                {} ({})".format(ssl, type(ssl)))
        display.v(" -> letsencrypt        {} ({})".format(letsencrypt, type(letsencrypt)))

        if mode == 'http' and (present and not ssl and not letsencrypt):
            result = True
        if mode == 'https' and (present and ssl and not letsencrypt):
            result = True
        if mode == 'acme' and (present and ssl and letsencrypt):
            result = True

        return result
