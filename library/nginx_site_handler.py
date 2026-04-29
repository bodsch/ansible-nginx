#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2022-2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
Ansible module ``nginx_site_handler`` – manage nginx vhost symlinks.

This module controls whether individual nginx vhost configuration files are
*enabled* (symlinked into ``sites-enabled``), *disabled* (symlink removed),
or *absent* (symlink removed **and** configuration file deleted from
``sites-available``).

Directory layout assumed
------------------------
::

    <nginx_base>/
        sites-available/   ← canonical vhost .conf files live here
        sites-enabled/     ← symlinks pointing into sites-available

Both directories are derived from ``site_path`` when provided, or fall back
to the Debian/Ubuntu defaults ``/etc/nginx/sites-{available,enabled}``.

Input flexibility
-----------------
The ``vhosts`` parameter is accepted as either a ``dict`` (keyed by vhost
name) or a ``list`` of vhost objects.  Behaviour is identical for both forms;
the internal :meth:`NginxSiteHandler._process_vhost` dispatcher handles both
after the name and filename have been extracted.

Idempotency
-----------
* ``enable_site`` – a correct symlink is left untouched (``changed=False``).
  A missing or stale symlink is (re-)created.
* ``disable_site`` – a non-existent symlink is a no-op (``changed=False``).
* ``remove_site`` – removes the symlink **and** the file in
  ``sites-available``; both operations are individually idempotent.
"""

from __future__ import absolute_import, annotations, print_function

import os
from typing import Any, Dict, List, Optional, Union

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.file import (
    create_link,
    remove_file,
)
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results

# ---------------------------------------------------------------------------

DOCUMENTATION = r"""
---
module: nginx_site_handler
version_added: "0.10.0"
author:
  - "Bodo Schulz (@bodsch) <me+ansible@bodsch.me>"

short_description: Enable, disable, or remove nginx vhost configuration files.

description:
  - Manages the symlink lifecycle of nginx vhost C(.conf) files between
    C(sites-available) and C(sites-enabled).
  - A vhost is I(enabled) by creating a symlink in C(sites-enabled) pointing
    to the corresponding file in C(sites-available).
  - A vhost is I(disabled) by removing that symlink.
  - A vhost is I(absent) when both the symlink and the C(sites-available)
    source file are deleted.
  - The module is fully idempotent: operations that would not change the
    filesystem state return C(changed=false).

options:
  vhosts:
    description:
      - Vhost configuration.  Accepted as either a C(dict) (keyed by vhost
        name) or a C(list) of vhost objects.
      - Each entry may contain C(filename) (defaults to C(<name>.conf)),
        C(enabled) (bool, defaults to C(true)), and C(state)
        (C(present) or C(absent), defaults to C(present)).
    type: raw
    required: true

  state:
    description:
      - Module-level desired state used in combination with the per-vhost
        C(state) key.
      - When both the module-level I(state) and the per-vhost I(state) are
        C(absent), the vhost symlink and its C(sites-available) source file
        are deleted.
    type: str
    required: false
    default: present
    choices: [absent, present]

  enabled:
    description:
      - Module-level enable flag.  A vhost is enabled only when both this
        flag and the per-vhost C(enabled) key are C(true).  A vhost is
        disabled only when both are C(false).
    type: bool
    required: false

  site_path:
    description:
      - Base directory for the nginx site configuration.  When provided,
        C(sites-available) and C(sites-enabled) are derived as
        C(<site_path>/sites-available) and C(<site_path>/sites-enabled).
      - Defaults to C(/etc/nginx) when omitted or empty.
    type: str
    required: false
    default: ""
"""

EXAMPLES = r"""
- name: Enable a vhost (dict representation)
  nginx_site_handler:
    enabled: true
    state: present
    vhosts:
      myapp:
        filename: myapp.conf
        enabled: true
        state: present

- name: Disable a vhost
  nginx_site_handler:
    enabled: false
    state: present
    vhosts:
      myapp:
        enabled: false

- name: Remove a vhost completely
  nginx_site_handler:
    state: absent
    vhosts:
      myapp:
        state: absent

- name: Enable vhosts (list representation)
  nginx_site_handler:
    enabled: true
    state: present
    vhosts:
      - name: myapp
        filename: myapp.conf
        enabled: true
      - name: api
        enabled: true

- name: Use a custom nginx base path
  nginx_site_handler:
    enabled: true
    site_path: /usr/local/etc/nginx
    vhosts:
      myapp:
        enabled: true
"""

RETURN = r"""
changed:
  description: Whether any symlink or file was created, updated, or removed.
  type: bool
  returned: always

failed:
  description: Whether the module encountered an unrecoverable error.
  type: bool
  returned: always

state:
  description: >
    List of per-vhost outcome dicts describing what action was taken.
    Only vhosts that triggered a change are included.
  type: list
  returned: always
"""

# ---------------------------------------------------------------------------

#: Nginx base path used when ``site_path`` is not specified.
_DEFAULT_NGINX_BASE: str = "/etc/nginx"


class NginxSiteHandler:
    """Manage nginx vhost symlinks between sites-available and sites-enabled.

    Attributes:
        module: The :class:`AnsibleModule` instance provided by Ansible.
        state: Module-level desired state (``"present"`` or ``"absent"``).
        enabled: Module-level enable flag (may be ``None`` when not set).
        vhosts: Raw vhost configuration (dict or list).
        site_available: Absolute path to the ``sites-available`` directory.
        site_enabled: Absolute path to the ``sites-enabled`` directory.
    """

    def __init__(self, module: AnsibleModule) -> None:
        """Initialise from Ansible module parameters.

        Args:
            module: Fully initialised :class:`AnsibleModule` instance.
        """
        self.module = module
        self.state: str = module.params.get("state") or "present"
        self.enabled: Optional[bool] = module.params.get("enabled")
        self.vhosts: Union[Dict[str, Any], List[Any]] = module.params["vhosts"]

        base = module.params.get("site_path") or _DEFAULT_NGINX_BASE
        self.site_available: str = os.path.join(base, "sites-available")
        self.site_enabled: str = os.path.join(base, "sites-enabled")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """Iterate over all vhosts and apply the requested state.

        Returns:
            Ansible result dict with keys ``changed``, ``failed``, ``state``.
        """
        result_state: List[Dict[str, Any]] = []

        if isinstance(self.vhosts, dict):
            for vhost_name, vhost_cfg in self.vhosts.items():
                file_name: str = vhost_cfg.get("filename") or f"{vhost_name}.conf"
                enabled: bool = vhost_cfg.get("enabled", True)
                vhost_state: str = vhost_cfg.get("state", "present")

                outcome = self._process_vhost(
                    vhost_name, file_name, enabled, vhost_state
                )
                if outcome:
                    result_state.append(outcome)

        elif isinstance(self.vhosts, list):
            for entry in self.vhosts:
                vhost_name = entry.get("name") or ""
                file_name = entry.get("filename") or f"{vhost_name}.conf"
                enabled = entry.get("enabled", True)
                vhost_state = entry.get("state", "present")

                outcome = self._process_vhost(
                    vhost_name, file_name, enabled, vhost_state
                )
                if outcome:
                    result_state.append(outcome)

        _state, _changed, _failed, state, changed, failed = results(
            self.module, result_state
        )

        return dict(changed=_changed, failed=False, state=result_state)

    # ------------------------------------------------------------------
    # Public vhost operations
    # ------------------------------------------------------------------

    def disable_site(self, file_name: str) -> bool:
        """Remove the symlink for *file_name* from ``sites-enabled``.

        Args:
            file_name: Configuration file name (e.g. ``"myapp.conf"``).

        Returns:
            ``True`` when the symlink was removed, ``False`` when it did
            not exist (idempotent no-op).
        """
        site_file = os.path.join(self.site_enabled, file_name)
        return remove_file(site_file)

    def enable_site(self, file_name: str) -> bool:
        """Create a symlink in ``sites-enabled`` pointing to ``sites-available``.

        The symlink is left untouched when it already exists and points to
        the correct target.  A stale or missing symlink is (re-)created.

        Logic overview::

            destination already a correct symlink → return False (no change)
            destination is a stale symlink        → recreate with force=True
            destination does not exist            → create normally

        Args:
            file_name: Configuration file name (e.g. ``"myapp.conf"``).

        Returns:
            ``True`` when the symlink was created or updated, ``False`` when
            it was already correct.
        """
        source = os.path.join(self.site_available, file_name)
        destination = os.path.join(self.site_enabled, file_name)

        # Fast-path: symlink exists and points to the correct target.
        if os.path.islink(destination) and os.readlink(destination) == source:
            return False

        # If destination is a stale symlink (wrong target), overwrite it.
        # If it does not exist at all, create it normally (force=False).
        force = os.path.islink(destination)
        if force:
            self.module.log(msg=f"replacing stale symlink '{destination}' → '{source}'")

        create_link(source, destination, force)
        return True

    def remove_site(self, file_name: str) -> bool:
        """Disable a vhost **and** delete its ``sites-available`` source file.

        The disable step (symlink removal) is always attempted first.
        ``changed`` reflects whether the ``sites-available`` source file
        itself was removed, as that is the irreversible part of the operation.

        Args:
            file_name: Configuration file name (e.g. ``"myapp.conf"``).

        Returns:
            ``True`` when the ``sites-available`` source file was deleted.
        """
        self.disable_site(file_name)
        source = os.path.join(self.site_available, file_name)
        return remove_file(source)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _process_vhost(
        self,
        name: str,
        file_name: str,
        enabled: bool,
        vhost_state: str,
    ) -> Optional[Dict[str, Any]]:
        """Evaluate and apply the desired state for a single vhost.

        This method consolidates the three mutually relevant conditions
        (disable / enable / remove) that were previously duplicated across
        the dict- and list-branches of :meth:`run`.

        Priority order:

        1. **Remove** – when both the module-level ``state`` and the
           per-vhost ``state`` are ``"absent"``.  This takes precedence over
           the ``enabled`` flags.
        2. **Disable** – when both the module-level ``enabled`` and the
           per-vhost ``enabled`` are falsy.
        3. **Enable** – when both the module-level ``enabled`` and the
           per-vhost ``enabled`` are truthy.

        Args:
            name: Vhost identifier used in log messages and result keys.
            file_name: Configuration file name (e.g. ``"myapp.conf"``).
            enabled: Per-vhost ``enabled`` flag from the vhost configuration.
            vhost_state: Per-vhost ``state`` value (``"present"`` or
                ``"absent"``).

        Returns:
            A single-key dict ``{name: {"state": <message>}}`` when an action
            was performed, or ``None`` when the vhost required no change.
        """
        # 1. Remove (highest priority – state=absent on both levels)
        if self.state == "absent" and vhost_state == "absent":
            if self.remove_site(file_name):
                return {
                    name: {"state": f"vhost {name} successfully disabled and removed"}
                }

        # 2. Disable
        elif not self.enabled and not enabled:
            if self.disable_site(file_name):
                return {name: {"state": f"vhost {name} successfully disabled"}}

        # 3. Enable
        elif self.enabled and enabled:
            if self.enable_site(file_name):
                return {name: {"state": f"vhost {name} successfully enabled"}}

        return None


# ---------------------------------------------------------------------------


def main() -> None:
    """Module entry point.  Called by Ansible at runtime."""
    args: Dict[str, Any] = dict(
        state=dict(
            required=False,
            default="present",
            choices=["absent", "present"],
        ),
        enabled=dict(
            required=False,
            type="bool",
        ),
        vhosts=dict(
            required=True,
            type="raw",
        ),
        site_path=dict(
            required=False,
            type="str",
            default="",
        ),
    )

    module = AnsibleModule(argument_spec=args, supports_check_mode=True)

    p = NginxSiteHandler(module)
    result = p.run()

    module.exit_json(**result)


if __name__ == "__main__":
    main()
