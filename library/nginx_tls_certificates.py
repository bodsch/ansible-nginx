#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
Ansible module ``nginx_tls_certificates`` – audit TLS certificate file presence.

This module inspects a vhost configuration and collects all TLS certificate
and private-key paths referenced under ``ssl.certificate`` and
``ssl.certificate_key``.  It then checks whether each file exists on the
target host and annotates the original vhost structure with a ``state`` key
so downstream tasks can react accordingly.

Reported states per vhost
--------------------------
``present``
    Both certificate and key file are present on disk.
``missing``
    Both certificate and key file are absent from disk.
``partial``
    One of the two files exists but the other does not.  This indicates a
    deployment problem and should be treated as an error in the calling role.
``n/a``
    The vhost has no SSL configuration or SSL is disabled.

Input flexibility
-----------------
Both the ``dict`` and ``list`` representations of the vhosts variable are
accepted.
"""

from __future__ import absolute_import, annotations, print_function

import os
from typing import Any, Dict, List, Optional, Tuple, Union

from ansible.module_utils.basic import AnsibleModule

# ---------------------------------------------------------------------------

DOCUMENTATION = r"""
---
module: nginx_tls_certificates
version_added: "0.10.0"
author:
  - "Bodo Schulz (@bodsch) <me+ansible@bodsch.me>"

short_description: Audit TLS certificate and key file presence for nginx vhosts.

description:
  - Collects all TLS certificate and private-key paths from a vhost
    configuration and verifies whether each file exists on the target host.
  - Annotates each vhost entry with a C(ssl.state) key
    (C(present), C(missing), or C(partial)).
  - Does not create or modify any files; this module is purely informational.

options:
  vhosts:
    description:
      - Vhost configuration.  Accepted as either a C(dict) (keyed by vhost
        name) or a C(list) of vhost objects.  Each vhost may contain an
        C(ssl) sub-key with C(enabled), C(certificate), and
        C(certificate_key) fields.
    type: raw
    required: true
"""

EXAMPLES = r"""
- name: Check TLS certificate availability
  nginx_tls_certificates:
    vhosts:
      mysite:
        ssl:
          enabled: true
          certificate: /etc/ssl/certs/mysite.crt
          certificate_key: /etc/ssl/private/mysite.key

- name: Check TLS certificates (list representation)
  nginx_tls_certificates:
    vhosts:
      - ssl:
          enabled: true
          certificate: /etc/ssl/certs/app.crt
          certificate_key: /etc/ssl/private/app.key
"""

RETURN = r"""
failed:
  description: Always C(false); this module does not fail on missing files.
  type: bool
  returned: always

missing_certs:
  description: List of certificate or key paths that do not exist on disk.
  type: list
  returned: always

present_certs:
  description: List of certificate or key paths that exist on disk.
  type: list
  returned: always

https_vhosts:
  description: >
    The original vhost structure annotated with C(ssl.state) per entry.
    Mirrors the type (dict or list) of the C(vhosts) input.
  type: raw
  returned: always
"""

# ---------------------------------------------------------------------------

#: Sentinel for a vhost without valid SSL configuration.
_SSL_STATE_NA = "n/a"
#: Both certificate and key are present on disk.
_SSL_STATE_PRESENT = "present"
#: Both certificate and key are absent from disk.
_SSL_STATE_MISSING = "missing"
#: Exactly one of certificate / key is present – indicates a deployment issue.
_SSL_STATE_PARTIAL = "partial"


class NginxTLSCerts:
    """Audit TLS certificate and key file presence for nginx vhosts.

    Attributes:
        module: The :class:`AnsibleModule` instance provided by Ansible.
        vhosts: Raw vhost configuration (dict or list).
    """

    def __init__(self, module: AnsibleModule) -> None:
        """Initialise from Ansible module parameters.

        Args:
            module: Fully initialised :class:`AnsibleModule` instance.
        """
        self.module = module
        self.vhosts: Union[Dict[str, Any], List[Any]] = module.params["vhosts"]

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """Collect all TLS paths, verify existence and annotate the vhosts.

        Returns:
            Ansible result dict with keys ``failed``, ``missing_certs``,
            ``present_certs``, and ``https_vhosts``.
        """
        unique_files = self._collect_tls_paths()

        missing: List[str] = [f for f in unique_files if not os.path.exists(f)]
        present: List[str] = [f for f in unique_files if os.path.exists(f)]

        annotated_vhosts = self._annotate_tls_state(missing, present)

        return dict(
            failed=False,
            missing_certs=missing,
            present_certs=present,
            https_vhosts=annotated_vhosts,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collect_tls_paths(self) -> List[str]:
        """Extract unique TLS file paths from all SSL-enabled vhosts.

        Only vhosts where ``ssl.enabled`` is truthy are considered.
        Order is preserved; duplicates are removed via ``dict.fromkeys``.

        Returns:
            Deduplicated list of absolute certificate / key paths.
        """
        raw_paths: List[str] = []

        if isinstance(self.vhosts, dict):
            for _vhost, values in self.vhosts.items():
                cert, key = self._ssl_pair(values)
                if cert:
                    raw_paths.append(cert)
                if key:
                    raw_paths.append(key)

        elif isinstance(self.vhosts, list):
            for entry in self.vhosts:
                if not entry.get("ssl", {}).get("enabled"):
                    continue
                cert, key = self._ssl_pair(entry)
                if cert:
                    raw_paths.append(cert)
                if key:
                    raw_paths.append(key)

        return list(dict.fromkeys(raw_paths))

    def _annotate_tls_state(
        self,
        missing: List[str],
        present: List[str],
    ) -> Union[Dict[str, Any], List[Any]]:
        """Annotate each vhost with a ``ssl.state`` describing file availability.

        Args:
            missing: File paths that do not exist on disk.
            present: File paths that exist on disk.

        Returns:
            Annotated copy of the vhost structure in its original type
            (dict or list).
        """
        if isinstance(self.vhosts, dict):
            data: Dict[str, Any] = self.vhosts.copy()
            for key, values in data.items():
                cert, cert_key = self._ssl_pair(values)
                if cert and cert_key:
                    data[key].setdefault("ssl", {})["state"] = self._tls_state(
                        cert, cert_key, missing, present
                    )

        elif isinstance(self.vhosts, list):
            data = []
            for entry in self.vhosts:
                entry = entry.copy()
                cert, cert_key = self._ssl_pair(entry)
                if cert and cert_key:
                    entry.setdefault("ssl", {})["state"] = self._tls_state(
                        cert, cert_key, missing, present
                    )
                data.append(entry)

        else:
            data = self.vhosts  # type: ignore[assignment]

        return data

    @staticmethod
    def _ssl_pair(vhost_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """Extract the certificate and key paths from a single vhost dict.

        Args:
            vhost_data: A single vhost configuration dict.

        Returns:
            A 2-tuple ``(certificate_path, key_path)``.  Either element may
            be ``None`` if the corresponding key is absent or SSL is disabled.
        """
        ssl: Dict[str, Any] = vhost_data.get("ssl", {})
        if not ssl.get("enabled", False):
            return None, None
        return ssl.get("certificate"), ssl.get("certificate_key")

    @staticmethod
    def _tls_state(
        cert: str,
        key: str,
        missing: List[str],
        present: List[str],
    ) -> str:
        """Determine the TLS state for a single cert/key pair.

        Args:
            cert: Absolute path to the certificate file.
            key: Absolute path to the private key file.
            missing: All paths known to be absent.
            present: All paths known to be present.

        Returns:
            One of :data:`_SSL_STATE_PRESENT`, :data:`_SSL_STATE_MISSING`,
            or :data:`_SSL_STATE_PARTIAL`.
        """
        cert_ok = cert in present
        key_ok = key in present

        if cert_ok and key_ok:
            return _SSL_STATE_PRESENT
        if not cert_ok and not key_ok:
            return _SSL_STATE_MISSING
        return _SSL_STATE_PARTIAL


# ---------------------------------------------------------------------------


def main() -> None:
    """Module entry point.  Called by Ansible at runtime."""
    args: Dict[str, Any] = dict(
        vhosts=dict(required=True, type="raw"),
    )

    module = AnsibleModule(argument_spec=args, supports_check_mode=True)

    p = NginxTLSCerts(module)
    result = p.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


if __name__ == "__main__":
    main()
