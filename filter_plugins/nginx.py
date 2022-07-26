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
            'activate_vhost_by': self.activate_vhost_by,
            # 'letsencrypt': self.letsencrypt,
            'create_vhost': self.create_vhost,
            'vhost_directory': self.vhost_directory,
            'htpasswd': self.htpasswd,
            'http_vhosts': self.http_vhosts,
            'https_vhosts': self.https_vhosts,
        }

    def activate_vhost_by(self, data=None, mode='http'):  # certificate_exists=False):
        """
        """
        display.v(" = activate_vhost_by(data, {}))".format(mode))
        display.v("   {}".format(data.get('key', "")))

        result = False
        enabled = True
        present = True

        display.v("   - enabled            {}".format(enabled))
        display.v("   - present            {}".format(present))

        value = data.get('value', {})

        if enabled and present:
            result = True

        #if mode == 'http' and present:
        #    result = True

        if mode == 'https':
            le_enabled = False
            ssl = value.get("ssl", False)

            certificate_exists = value.get("ssl_certificate_exists", False)

            letsencrypt = value.get("letsencrypt", {})

            if letsencrypt:
                le_enabled  = letsencrypt.get('enabled', False)
                le_email    = letsencrypt.get('email', "")

            display.v("   - certificate_exists {}".format(certificate_exists))
            display.v("   - ssl                {}".format(ssl))
            display.v("   - letsencrypt        {}".format(le_enabled))

            display.v("   - x                  {}".format(not certificate_exists and (not ssl or not le_enabled)))

            if not certificate_exists and (not ssl or not le_enabled):
                result = False

                #if certificate_exists and not le_enabled:
                #    result = False

        display.v(" = result {}".format(result))

        return result

    def letsencrypt(self, data):
        """
        """
        display.v(" = letsencrypt({}) - ({})".format(json.dumps(data, indent=2), type(data)))

        result = {}

        for k, v in data.items():
            display.v(" = data {} ({})".format(json.dumps(v, indent=2), type(v)))
            if v.get('letsencrypt', {}):
                result[k] = dict(
                    domains=v.get('domains', []),
                    email=v.get('letsencrypt', {}).get('email', '')
                )

        display.v(" = result {}".format(result))

        return result

    def create_vhost(self, data, mode='http'):
        """
        """
        display.v(" = create_vhost(data, {})".format(mode))
        # display.v(" = create_vhost({}, {}) -  ({})".format(json.dumps(data, indent=2), mode, type(data)))
        display.v("   {}".format(data.get('key', "")))

        result = False
        present = True
        letsencrypt = False

        value = data.get('value', {})

        state = value.get("state", True)
        ssl = value.get("ssl", {})
        if value.get("letsencrypt", {}):
            letsencrypt = value.get("letsencrypt", {}).get("enabled", False)

        display.v("    - present            {}".format(present))
        #display.v("    - ssl                {}".format(ssl))
        #display.v("    - letsencrypt        {}".format(letsencrypt))

        if mode == 'http' and (present and not ssl and not letsencrypt):
            result = True
        if mode == 'https' and (present and ssl and not letsencrypt):
            result = True
        if mode == 'acme' and (present and ssl and letsencrypt):
            result = True

        display.v(" = result {}".format(result))

        return result

    def vhost_directory(self, data, directory):
        """
          return a list of directories for keyword like 'root', access_log or others
        """
        display.v(" = vhost_directory(data, {})".format(directory))

        # format(json.dumps(data, indent=2)

        result = []

        for item in data:
            for k, v in item.items():
                if k == "value":
                    if v.get(directory, None):
                        result.append(v.get(directory))

        display.v(" = result {}".format(result))

        return result


    def htpasswd(self, data):
        """
        """
        display.v(" = htpasswd(data)")
        result = {}

        if isinstance(data, dict):
            """
            """
            for k, v in data.items():
                htpasswd = v.get('htpasswd', None)
                if htpasswd:
                    result[k] = htpasswd

        display.v(" = result {}".format(result))

        return result


    def http_vhosts(self, data):
        """
        """
        results = []
        display.v(" = http_vhosts(data)")
        # display.v(" = data {} -  ({})".format(json.dumps(data, indent=2), type(data)))

        _data = data.copy()

        for k, v in _data.items():
            ssl = v.get('ssl', {})
            enabled = ssl.get("enabled", False)
            # display.v(f"   - {k} : {len(ssl)} : {ssl} ")

            if len(ssl) > 0 and enabled:
                _ = data.pop(k)

        # display.v("-----------------------------------")
        # for k, v in data.items():
        #     display.v(f"   - {k}")
        # display.v("-----------------------------------")

        return data

    def https_vhosts(self, data):
        """
        """
        results = []
        display.v(" = https_vhosts(data)")

        _data = data.copy()

        for k, v in _data.items():
            ssl = v.get('ssl', {})
            enabled = ssl.get("enabled", False)
            # display.v(f"   - {k} : {len(ssl)} : {ssl} ")

            if not(len(ssl) > 0 and enabled):
                _ = data.pop(k)

        # display.v("-----------------------------------")
        # for k, v in data.items():
        #     display.v(f"   - {k}")
        # display.v("-----------------------------------")
        return data