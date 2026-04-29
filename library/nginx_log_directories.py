#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2026, Bodo Schulz <me+ansible@bodsch.me>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
Ansible module ``nginx_log_directories`` – ensure nginx vhost log directories exist.

This module inspects a vhost configuration (either a ``dict`` keyed by vhost
name or a ``list`` of vhost objects) and creates all required log directories
with the specified ownership and permissions.

Idempotency
-----------
A directory that already exists is not re-created.  Ownership / mode is
applied on every run so that drift is corrected automatically.

Input flexibility
-----------------
Both the ``dict`` and ``list`` representations of the vhosts variable are
accepted so the module works regardless of how the calling role structures
its data.
"""

from __future__ import absolute_import, annotations, print_function

import os
from typing import Any, Dict, List, Tuple, Union

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.directory import (
    create_directory,
    fix_ownership,
)
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results

# ---------------------------------------------------------------------------

DOCUMENTATION = r"""
---
module: nginx_log_directories
version_added: "0.10.0"
author:
  - "Bodo Schulz (@bodsch) <me+ansible@bodsch.me>"

short_description: Create and fix ownership of nginx vhost log directories.

description:
  - Iterates over all configured vhosts and extracts the parent directories
    of access and error log paths.
  - Creates any directory that does not yet exist.
  - Applies the requested ownership and mode on every run so that drift is
    corrected automatically.

options:
  vhosts:
    description:
      - Vhost configuration.  Accepted as either a C(dict) (keyed by vhost
        name) or a C(list) of vhost objects.  Each vhost may contain a
        C(logfiles) sub-key with C(access.file) and/or C(error.file) paths.
    type: raw
    required: true

  owner:
    description:
      - Owner username for the log directories.
    type: str
    required: false

  group:
    description:
      - Group name for the log directories.
    type: str
    required: false

  mode:
    description:
      - Permission mode for the log directories (e.g. C("0755")).
    type: raw
    required: false
    default: "0755"
"""

EXAMPLES = r"""
- name: Ensure nginx log directories exist (dict vhosts)
  nginx_log_directories:
    vhosts:
      mysite:
        logfiles:
          access:
            file: /var/log/nginx/mysite/access.log
          error:
            file: /var/log/nginx/mysite/error.log
    owner: www-data
    group: www-data
    mode: "0750"

- name: Ensure nginx log directories exist (list vhosts)
  nginx_log_directories:
    vhosts:
      - logfiles:
          access:
            file: /var/log/nginx/app/access.log
          error:
            file: /var/log/nginx/app/error.log
    owner: www-data
    group: adm
"""

RETURN = r"""
changed:
  description: Whether any directory was created or had its ownership corrected.
  type: bool
  returned: always

failed:
  description: Whether the module encountered an unrecoverable error.
  type: bool
  returned: always

state:
  description: List of dicts describing each directory that was acted upon.
  type: list
  returned: always
"""

# ---------------------------------------------------------------------------


class NginxLogDirectories:
    """Ensure all nginx vhost log directories exist with correct ownership.

    Attributes:
        module: The :class:`AnsibleModule` instance provided by Ansible.
        vhosts: Raw vhost configuration (dict or list).
        owner: Desired directory owner username.
        group: Desired directory group name.
        mode: Desired directory permission mode string.
    """

    def __init__(self, module: AnsibleModule) -> None:
        """Initialise from Ansible module parameters.

        Args:
            module: Fully initialised :class:`AnsibleModule` instance.
        """
        self.module = module
        self.vhosts: Union[Dict[str, Any], List[Any]] = module.params["vhosts"]
        self.owner: str = module.params.get("owner") or ""
        self.group: str = module.params.get("group") or ""
        self.mode: str = str(module.params.get("mode") or "0755")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """Collect unique log directories, create them and fix ownership.

        Returns:
            Ansible result dict with keys ``changed``, ``failed``, ``state``.
        """
        unique_dirs = self._collect_log_directories()
        result_state: List[Dict[str, Any]] = []

        for directory in unique_dirs:
            d_created, d_ownership, state_msg = self._ensure_directory(directory)

            if d_created or d_ownership:
                result_state.append({directory: {"state": state_msg}})

        _state, _changed, _failed, state, changed, failed = results(
            self.module, result_state
        )

        return dict(changed=_changed, failed=False, state=result_state)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collect_log_directories(self) -> List[str]:
        """Extract unique parent directories of all configured log files.

        Handles both ``dict`` and ``list`` representations of the vhosts
        parameter.  Order is preserved; duplicates are removed.

        Returns:
            Deduplicated list of absolute directory paths.
        """
        raw_dirs: List[str] = []

        if isinstance(self.vhosts, dict):
            for _vhost, values in self.vhosts.items():
                raw_dirs.extend(self._dirs_from_logfiles(values.get("logfiles", {})))

        elif isinstance(self.vhosts, list):
            for entry in self.vhosts:
                raw_dirs.extend(self._dirs_from_logfiles(entry.get("logfiles", {})))

        # Preserve insertion order while deduplicating (dict.fromkeys is the
        # idiomatic O(n) approach; set() would be non-deterministic).
        return list(dict.fromkeys(raw_dirs))

    @staticmethod
    def _dirs_from_logfiles(logfiles: Dict[str, Any]) -> List[str]:
        """Return the parent directories of access and error log paths.

        Args:
            logfiles: Dict optionally containing ``access.file`` and/or
                ``error.file`` keys.

        Returns:
            List of directory paths (0, 1, or 2 entries).
        """
        dirs: List[str] = []
        for key in ("access", "error"):
            file_path: str = logfiles.get(key, {}).get("file", "")
            if file_path:
                dirs.append(os.path.dirname(file_path))
        return dirs

    def _ensure_directory(self, directory: str) -> Tuple[bool, bool, str]:
        """Create *directory* if absent and apply ownership / mode.

        Args:
            directory: Absolute path of the directory to manage.

        Returns:
            A 3-tuple ``(created, ownership_changed, human_readable_state)``.
        """
        d_created = False
        d_ownership = False

        if not os.path.exists(directory):
            d_created = create_directory(directory)

        d_ownership, _error_msg = fix_ownership(
            directory, self.owner, self.group, self.mode
        )

        if d_created and d_ownership:
            state_msg = "directory created and ownership fixed"
        elif d_created:
            state_msg = "directory successfully created"
        elif d_ownership:
            state_msg = "ownership corrected"
        else:
            state_msg = "no change required"

        return d_created, d_ownership, state_msg


# ---------------------------------------------------------------------------


def main() -> None:
    """Module entry point.  Called by Ansible at runtime."""
    args: Dict[str, Any] = dict(
        vhosts=dict(required=True, type="raw"),
        owner=dict(required=False, type="str"),
        group=dict(required=False, type="str"),
        mode=dict(required=False, type="raw", default="0755"),
    )

    module = AnsibleModule(argument_spec=args, supports_check_mode=True)

    p = NginxLogDirectories(module)
    result = p.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


if __name__ == "__main__":
    main()
