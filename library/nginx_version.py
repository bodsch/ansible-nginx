#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
Ansible module ``nginx_version`` – detect the installed nginx version.

The module runs ``nginx -v`` and parses the version string from stderr
(nginx writes its version info to stderr by design).  The extracted version
string is returned as a plain dotted string, e.g. ``"1.25.3"``.

A sentinel value of ``"0.0.0"`` is returned when the binary cannot be found
or the output does not match the expected pattern, allowing the calling role
to detect the failure condition without the module raising an error.
"""

from __future__ import absolute_import, annotations, print_function

import re
from typing import Any, Dict, List, Tuple

from ansible.module_utils.basic import AnsibleModule

# ---------------------------------------------------------------------------

DOCUMENTATION = r"""
---
module: nginx_version
version_added: "0.10.0"
author:
  - "Bodo Schulz (@bodsch) <me+ansible@bodsch.me>"

short_description: Return the installed nginx version as a string.

description:
  - Locates the C(nginx) binary via Ansible's C(get_bin_path) and runs
    C(nginx -v) to extract the version number from stderr.
  - Returns C("0.0.0") when the binary is missing or the version cannot be
    parsed, so callers can handle the absence gracefully.

notes:
  - nginx writes version information to B(stderr), not stdout.  The module
    reads C(err) accordingly.
"""

EXAMPLES = r"""
- name: Get nginx version
  nginx_version:
  register: _nginx_version

- name: Show version
  ansible.builtin.debug:
    msg: "nginx {{ _nginx_version.version }} is installed"
"""

RETURN = r"""
changed:
  description: Always C(false); this module never modifies state.
  type: bool
  returned: always

failed:
  description: Always C(false); parse failures return the sentinel C("0.0.0").
  type: bool
  returned: always

rc:
  description: Return code of the C(nginx -v) invocation.
  type: int
  returned: always

version:
  description: >
    Dotted version string (e.g. C("1.25.3")).  Returns C("0.0.0") when the
    binary is not found or the output cannot be parsed.
  type: str
  returned: always
"""

# ---------------------------------------------------------------------------

#: Sentinel returned when the nginx binary is absent or unparseable.
_FALLBACK_VERSION: str = "0.0.0"

# ``nginx -v`` writes to stderr:  "nginx version: nginx/1.25.3"
# The pattern anchors on the literal "nginx/" prefix and captures the
# dotted numeric version that follows.  re.DOTALL is intentionally omitted
# because the match is always on a single line.
_VERSION_RE = re.compile(r"nginx/(?P<version>[0-9]+(?:\.[0-9]+)*)")


class NginxVersion:
    """Detect the installed nginx version by invoking ``nginx -v``.

    Attributes:
        module: The :class:`AnsibleModule` instance provided by Ansible.
        nginx_bin: Absolute path to the ``nginx`` binary.
    """

    def __init__(self, module: AnsibleModule) -> None:
        """Locate the nginx binary and store module context.

        Args:
            module: Fully initialised :class:`AnsibleModule` instance.

        Raises:
            :class:`SystemExit`: Via Ansible's ``fail_json`` when the
                ``nginx`` binary cannot be found and ``get_bin_path``
                is called with ``required=True``.
        """
        self.module = module
        self.nginx_bin: str = module.get_bin_path("nginx", True)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """Execute ``nginx -v`` and return the parsed version.

        Returns:
            Ansible result dict with keys ``changed``, ``failed``,
            ``rc``, and ``version``.
        """
        rc, _out, err = self.__exec([self.nginx_bin, "-v"])

        match = _VERSION_RE.search(err.strip())
        version = match.group("version") if match else _FALLBACK_VERSION

        return dict(changed=False, failed=False, rc=rc, version=version)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def __exec(
        self,
        commands: List[str],
        check_rc: bool = False,
    ) -> Tuple[int, str, str]:
        """Run an external command via the Ansible module helper.

        All output is forwarded to the Ansible module log for debugging.

        Args:
            commands: Argv list to execute.
            check_rc: When ``True`` Ansible raises on non-zero exit codes.
                Defaults to ``False`` so that a missing or broken nginx
                binary is handled gracefully by the caller.

        Returns:
            A 3-tuple ``(rc, stdout, stderr)``.
        """
        rc, out, err = self.module.run_command(commands, check_rc=check_rc)

        return rc, out, err


# ---------------------------------------------------------------------------


def main() -> None:
    """Module entry point.  Called by Ansible at runtime."""
    module = AnsibleModule(argument_spec={}, supports_check_mode=True)

    p = NginxVersion(module)
    result = p.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


if __name__ == "__main__":
    main()
