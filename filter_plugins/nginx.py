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
            'activate_vhost_by': self.activate_vhost_by,
            # 'letsencrypt': self.letsencrypt,
            'create_vhost': self.create_vhost,
            'vhost_directory': self.vhost_directory,
            'vhost_listen': self.vhost_listen,
            'http_vhosts': self.http_vhosts,
            'https_vhosts': self.https_vhosts,
        }

    def activate_vhost_by(self, data, mode='http'):
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

        # if mode == 'http' and present:
        #    result = True

        if mode == 'https':
            le_enabled = False
            ssl = value.get("ssl", False)

            certificate_exists = value.get("ssl_certificate_exists", False)

            display.v("   - certificate_exists {}".format(certificate_exists))
            display.v("   - ssl                {}".format(ssl))
            display.v("   - x                  {}".format(not certificate_exists and not ssl))

            if not certificate_exists and (not ssl or not le_enabled):
                result = False

                # if certificate_exists and not le_enabled:
                #    result = False

        display.v(" = result {}".format(result))

        return result

    def create_vhost(self, data, mode='http'):
        """
        """
        display.v(" = create_vhost(data, {})".format(mode))
        display.v("   {}".format(data.get('key', "")))

        result = False
        present = True

        value = data.get('value', {})

        # state = value.get("state", True)
        ssl = value.get("ssl", {}).get("enabled", False)

        display.v("    - present            {}".format(present))

        if mode == 'http' and (present and not ssl):
            result = True
        if mode in ['https', 'acme'] and (present and ssl):
            result = True

        display.v(" = result {}".format(result))

        return result

    def vhost_directory(self, data, directory):
        """
          return a list of directories for keyword like 'root', access_log or others
        """
        result = []

        for item in data:
            for k, v in item.items():
                if k == "value":
                    if v.get(directory, None):
                        result.append(v.get(directory))

        # display.v(" = result {}".format(result))
        return result

    def vhost_listen(self, data, port, default):
        """
        """
        display.v(f"vhost_listen({port}, {default})")

        result = []

        if (isinstance(port, str) or isinstance(port, int)):
            result.append(port)

        if isinstance(port, list):
            result = port

        if default:
            result.append('default_server')

        display.v(f" = result {result}")

        return result



    def http_vhosts(self, data):
        """
        """
        _data = data.copy()

        for k, v in _data.items():
            ssl = v.get('ssl', {})
            enabled = ssl.get("enabled", False)

            if len(ssl) > 0 and enabled:
                _ = data.pop(k)

        return data

    def https_vhosts(self, data):
        """
        """
        _data = data.copy()

        for k, v in _data.items():
            ssl = v.get('ssl', {})
            enabled = ssl.get("enabled", False)

            if not(len(ssl) > 0 and enabled):
                _ = data.pop(k)

        return data
