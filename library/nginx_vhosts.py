#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2022-2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
Ansible module ``nginx_vhosts`` – render and deploy nginx vhost configurations.

This module is responsible for the full lifecycle of nginx virtual host
configuration files:

1. **Render** – a Jinja2 template (from ``sites-available`` sources) is
   rendered with per-vhost data, ACME settings, and the detected nginx
   version.
2. **Deploy** – the rendered content is written to
   ``/etc/nginx/sites-available/<name>.conf`` only when a checksum
   comparison detects a change (idempotent write).
3. **Enable / Disable** – a symlink in ``/etc/nginx/sites-enabled/`` is
   created or removed depending on the per-vhost ``enabled`` flag.
4. **Remove** – both the symlink and the ``sites-available`` source file
   are deleted when ``state: absent``.

Template rendering
------------------
All Jinja2 rendering logic – including the custom filters – is isolated in
:class:`VhostTemplateRenderer`.  The class registers the following custom
filters on the Jinja2 environment:

* ``bodsch.core.var_type`` / ``bodsch.core.type`` – return the Python type
  name of a value as a string.
* ``split`` – split a string, filtering empty tokens.
* ``regex_replace`` – ``re.sub`` wrapper.
* ``validate_listener`` – strip ``quic`` / ``reuseport`` tokens from nginx
  ``listen`` directives (for nginx versions that do not support them yet).
* ``version_compare`` – semantic version comparison using
  :mod:`packaging.version`.

TLS handling
------------
When ``ssl.enabled`` is ``true`` and ``ssl.state`` is ``missing``, the
module either warns (``ignore_missing_certificate: true``) or fails hard.
The HTTPS template is automatically selected when no explicit ``template``
key is provided and SSL is enabled.

Temporary directory
-------------------
Rendering is done to a per-PID temporary directory under ``/run/.ansible``
so that concurrent Ansible runs do not interfere.  The directory is removed
unconditionally at the end of :meth:`NginxVHosts.run`.
"""

from __future__ import absolute_import, annotations, print_function

import json
import operator
import os
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native, to_text
from ansible_collections.bodsch.core.plugins.module_utils.checksum import Checksum
from ansible_collections.bodsch.core.plugins.module_utils.directory import (
    create_directory,
)
from ansible_collections.bodsch.core.plugins.module_utils.file import (
    create_link,
    remove_file,
)
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results
from jinja2 import Environment, FileSystemLoader
from packaging.version import Version

# ---------------------------------------------------------------------------

DOCUMENTATION = r"""
---
module: nginx_vhosts
version_added: "0.10.0"
author:
  - "Bodo Schulz (@bodsch) <me+ansible@bodsch.me>"

short_description: Render, deploy, enable and disable nginx vhost configurations.

description:
  - Renders one Jinja2 template per vhost entry using per-vhost data, ACME
    settings, and the installed nginx version.
  - Writes the rendered content to C(sites-available) only when the content
    has actually changed (checksum-based idempotency).
  - Creates or removes a symlink in C(sites-enabled) based on the per-vhost
    C(enabled) flag.
  - Removes both the symlink and the C(sites-available) source file when
    C(state: absent).
  - The nginx version is read from the local Ansible facts file
    C(/etc/ansible/facts.d/nginx.fact) and exposed to templates as
    C(nginx_version).

notes:
  - This module is typically used in combination with M(nginx_tls_certificates),
    which pre-checks whether TLS certificate files are present on disk and
    annotates each vhost dict with C(ssl.state).  When C(ssl.state) is absent
    (e.g. on a first run without M(nginx_tls_certificates) in the play), the
    TLS guard is skipped and the vhost is activated optimistically.
  - Template selection priority for C(template) key is I(absent)
    1. Explicit C(template) key in the vhost dict.
    2. C(template.https) when C(ssl.enabled: true).
    3. C(template.http) otherwise.

options:
  vhosts:
    description:
      - List of vhost configuration dicts.
      - Each entry must contain at least a C(name) key.
    type: list
    elements: dict
    required: true
    suboptions:
      name:
        description:
          - Unique vhost identifier.  Used as the base name for the
            C(.conf) file (C(<name>.conf)) unless C(filename) is set.
        type: str
        required: true
      filename:
        description:
          - Override the generated C(.conf) file name.
          - When omitted the file is named C(<name>.conf).
        type: str
        required: false
      state:
        description:
          - C(present) – ensure the vhost configuration file exists and the
            symlink state matches C(enabled).
          - C(absent) – remove both the C(sites-enabled) symlink and the
            C(sites-available) source file.
        type: str
        required: false
        default: present
        choices: [present, absent]
      enabled:
        description:
          - When C(true), a symlink in C(sites-enabled) is created.
          - When C(false), the symlink is removed (vhost disabled but file
            kept in C(sites-available)).
        type: bool
        required: false
        default: true
      template:
        description:
          - Override the Jinja2 template file name for this vhost.
          - When omitted the default HTTP or HTTPS template is selected
            based on C(ssl.enabled).
        type: str
        required: false
      description:
        description:
          - Free-text description; passed through to the template as part
            of C(item) but otherwise unused by the module.
        type: str
        required: false
      domains:
        description:
          - List of domain names (C(server_name) values) for this vhost.
            Passed to the template as part of C(item).
        type: list
        elements: str
        required: false
      listen:
        description:
          - List of C(listen) directive values, e.g. C(["443 ssl http2",
            "8443 reuseport"]).  Passed to the template as part of C(item).
        type: list
        elements: str
        required: false
      root_directory:
        description:
          - Document root path for the vhost.  Passed to the template as
            part of C(item).
        type: str
        required: false
      root_directory_create:
        description:
          - When C(true), the calling role should ensure C(root_directory)
            is created.  Passed to the template as part of C(item);
            not acted upon by this module directly.
        type: bool
        required: false
        default: false
      locations:
        description:
          - Dict of nginx location blocks keyed by their path.  Passed
            to the template as part of C(item).
        type: dict
        required: false
      logfiles:
        description:
          - Log file configuration with sub-keys C(access) and C(error),
            each accepting C(file) and C(loglevel).  Passed to the
            template as part of C(item).
        type: dict
        required: false
      redirects:
        description:
          - List of redirect rules.  Each entry accepts C(location),
            C(return), and C(destination).  Passed to the template as
            part of C(item).
        type: list
        elements: dict
        required: false
      acme_challenge:
        description:
          - When C(true), the template should include the ACME challenge
            location block.  Passed to the template as part of C(item).
        type: bool
        required: false
        default: false
      ssl:
        description:
          - TLS configuration sub-dict.
        type: dict
        required: false
        suboptions:
          enabled:
            description:
              - Enable TLS for this vhost.  When C(true), the HTTPS
                default template is used unless C(template) is set
                explicitly.
            type: bool
            required: false
            default: false
          state:
            description:
              - Certificate availability state, typically set by the
                M(nginx_tls_certificates) module.
              - C(present) – certificate and key files are confirmed to
                exist on disk; the vhost is activated normally.
              - C(missing) – certificate and/or key files are confirmed
                to be absent; activation is blocked (see
                C(ignore_missing_certificate)).
              - When the key is B(absent) (not set), the state is unknown
                and the TLS guard is skipped.  The vhost is activated
                optimistically.  This is the expected behaviour on a
                first run before M(nginx_tls_certificates) has been
                executed.
            type: str
            required: false
            choices: [present, missing, partial]
          certificate:
            description: Absolute path to the TLS certificate file.
            type: str
            required: false
          certificate_key:
            description: Absolute path to the TLS private key file.
            type: str
            required: false
          dhparam:
            description: Absolute path to the Diffie-Hellman parameter file.
            type: str
            required: false
          ciphers:
            description:
              - Cipher suite identifier forwarded to the template.
            type: str
            required: false

  template:
    description:
      - Dict describing the default vhost templates and their location.
    type: dict
    required: true
    suboptions:
      path:
        description:
          - Absolute path to the directory containing the Jinja2
            template files.  Typically a remote temp directory populated
            by the calling role.
        type: str
        required: true
      http:
        description:
          - File name of the default HTTP vhost template
            (e.g. C(vhost_http.conf.j2)).
        type: str
        required: true
      https:
        description:
          - File name of the default HTTPS vhost template
            (e.g. C(vhost_https.conf.j2)).
        type: str
        required: true

  dest:
    description:
      - Target directory where rendered vhost C(.conf) files are written.
      - Corresponds to the nginx C(sites-available) directory.
    type: str
    required: false
    default: /etc/nginx/sites-available

  acme:
    description:
      - ACME / Let's Encrypt configuration passed verbatim into every
        Jinja2 template context as C(nginx_acme).
      - Typical keys are C(enabled) and C(challenge_directory).
    type: dict
    required: false

  ignore_missing_certificate:
    description:
      - Controls the behaviour when C(ssl.state) is explicitly C(missing).
      - When C(false) (default), the module returns a failure and the vhost
        is not activated.
      - When C(true), a warning message is returned and the vhost is skipped
        without failing the play.
      - Has no effect when C(ssl.state) is absent or C(present).
    type: bool
    required: false
    default: false
"""

EXAMPLES = r"""
# ---------------------------------------------------------------------------
# Minimal HTTP vhost (status endpoint)
# ---------------------------------------------------------------------------
- name: Create nginx status vhost
  nginx_vhosts:
    template:
      path: "{{ nginx_remote_tmp_directory }}/{{ ansible_facts.fqdn }}"
      http: "{{ nginx_vhost_templates.http }}"
      https: "{{ nginx_vhost_templates.https }}"
    vhosts:
      - name: nginx-status
        filename: 00-status.conf
        state: present
        enabled: true
        domains:
          - localhost
        listen:
          - 127.0.0.1:8088
        root_directory: /var/www/
        locations:
          "/nginx_status":
            options: |
              stub_status on;
              access_log off;
              allow 127.0.0.1;
              deny all;

# ---------------------------------------------------------------------------
# HTTP redirect vhost (ACME challenge + redirect to HTTPS)
# ---------------------------------------------------------------------------
- name: Create HTTP redirect vhost
  nginx_vhosts:
    template:
      path: "{{ nginx_remote_tmp_directory }}/{{ ansible_facts.fqdn }}"
      http: "{{ nginx_vhost_templates.http }}"
      https: "{{ nginx_vhost_templates.https }}"
    acme:
      enabled: true
      challenge_directory: /var/www
    vhosts:
      - name: 20-bar.docker.local
        state: present
        enabled: true
        domains:
          - bar.docker.local
          - docker.local
        acme_challenge: true
        redirects:
          - location: "/"
            return: 301
            destination: "https://$server_name$request_uri"

# ---------------------------------------------------------------------------
# HTTPS vhost
# ssl.state is set by nginx_tls_certificates before this task runs.
# When omitted (first run), the TLS guard is skipped and the vhost is
# activated optimistically.
# ---------------------------------------------------------------------------
- name: Create HTTPS vhost
  nginx_vhosts:
    template:
      path: "{{ nginx_remote_tmp_directory }}/{{ ansible_facts.fqdn }}"
      http: "{{ nginx_vhost_templates.http }}"
      https: "{{ nginx_vhost_templates.https }}"
    acme:
      enabled: true
      challenge_directory: /var/www
    ignore_missing_certificate: "{{ nginx_ignore_missing_certificate | bool }}"
    vhosts:
      - name: 40-bar.docker.local
        state: present
        enabled: true
        domains:
          - bar.docker.local
          - docker.local
        root_directory: /var/www/docker.local
        root_directory_create: true
        listen:
          - 443 ssl http2
          - 8443 reuseport
        logfiles:
          access:
            file: /var/log/nginx/bar.docker.local/access.log
            loglevel: json_combined
          error:
            file: /var/log/nginx/bar.docker.local/error.log
            loglevel: warn
        ssl:
          enabled: true
          ciphers: default
          certificate:     /etc/snakeoil/docker.local/docker.local.pem
          certificate_key: /etc/snakeoil/docker.local/docker.local.key
          dhparam:         /etc/snakeoil/docker.local/dh.pem

# ---------------------------------------------------------------------------
# Remove a vhost completely
# ---------------------------------------------------------------------------
- name: Remove obsolete vhost
  nginx_vhosts:
    template:
      path: "{{ nginx_remote_tmp_directory }}/{{ ansible_facts.fqdn }}"
      http: "{{ nginx_vhost_templates.http }}"
      https: "{{ nginx_vhost_templates.https }}"
    vhosts:
      - name: oldapp
        state: absent
"""

RETURN = r"""
changed:
  description: Whether any vhost file or symlink was created, updated, or removed.
  type: bool
  returned: always

failed:
  description: Whether the module encountered an unrecoverable error.
  type: bool
  returned: always

msg:
  description: >
    List of per-vhost outcome dicts.  Each dict is keyed by the vhost name
    and contains C(failed), C(changed), and C(msg) keys describing the
    result of that individual vhost operation.
  type: list
  elements: dict
  returned: always
  sample:
    - 40-bar.docker.local:
        failed: false
        changed: true
        msg: "The VHost was successfully changed. and enabled."
    - nginx-status:
        failed: false
        changed: false
        msg: "The VHost has not been changed."
"""

# ---------------------------------------------------------------------------
# Operator alias map used by the version_compare Jinja2 filter.
_OP_MAP: Dict[str, str] = {
    "==": "eq",
    "=": "eq",
    "eq": "eq",
    "<": "lt",
    "lt": "lt",
    "<=": "le",
    "le": "le",
    ">": "gt",
    "gt": "gt",
    ">=": "ge",
    "ge": "ge",
    "!=": "ne",
    "<>": "ne",
    "ne": "ne",
}

#: Per-PID working directory for temporary render output.
_TMP_BASE: str = "/run/.ansible"

#: Path to the local Ansible facts file written by the nginx role.
_FACTS_FILE: str = "/etc/ansible/facts.d/nginx.fact"


# ===========================================================================
# Template renderer
# ===========================================================================


class VhostTemplateRenderer:
    """Render an nginx vhost Jinja2 template to a string.

    This class encapsulates the entire Jinja2 rendering pipeline, including
    the registration of custom filters that mirror the behaviour of common
    Ansible / Jinja2 filter plugins.

    The class is intentionally stateless beyond what is passed to
    :meth:`__init__` so that it can be instantiated once per module run and
    reused for every vhost.

    Attributes:
        module: The :class:`AnsibleModule` instance (used for debug logging).
        template_path: Absolute path to the directory that contains vhost
            templates.
        acme: ACME configuration dict passed into the template context as
            ``nginx_acme``.
        nginx_version: Detected nginx version string (e.g. ``"1.25.3"``),
            passed into the template context as ``nginx_version``.
    """

    def __init__(
        self,
        module: AnsibleModule,
        template_path: str,
        acme: Optional[Dict[str, Any]],
        nginx_version: str,
    ) -> None:
        """Initialise the renderer.

        Args:
            module: Fully initialised :class:`AnsibleModule` instance.
            template_path: Absolute path to the vhost template directory.
            acme: ACME configuration dict (may be ``None``).
            nginx_version: Detected nginx version string.
        """
        self.module = module
        self.template_path = template_path
        self.acme = acme
        self.nginx_version = nginx_version

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def render(self, template_file: str, data: Dict[str, Any]) -> Optional[str]:
        """Render *template_file* with *data* and return the result string.

        The template is located by resolving the real path of *template_file*
        so that symlinked template directories are handled correctly.

        A Jinja2 :class:`~jinja2.Environment` with ``trim_blocks=True`` and
        ``lstrip_blocks=True`` is created for each call.  The following custom
        filters are registered on the environment before rendering:

        * ``bodsch.core.var_type`` / ``bodsch.core.type``
        * ``split``
        * ``regex_replace``
        * ``validate_listener``
        * ``version_compare``

        Args:
            template_file: Absolute path to the Jinja2 template file.
            data: Per-vhost data dict; passed into the template as ``item``.

        Returns:
            Rendered template string, or ``None`` when *template_file* does
            not exist or is not a regular file.
        """
        self.module.log(
            f"VhostTemplateRenderer::render(template_file: {template_file})"
        )

        if not os.path.isfile(template_file):
            return None

        real_path = os.path.realpath(template_file)
        file_dir = os.path.dirname(real_path)
        file_name = os.path.basename(real_path)

        env = Environment(
            loader=FileSystemLoader(file_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        env.filters.update(
            {
                "bodsch.core.var_type": self._filter_var_type,
                "bodsch.core.type": self._filter_var_type,
                "split": self._filter_split,
                "regex_replace": self._filter_regex_replace,
                "validate_listener": self._filter_validate_listener,
                "version_compare": self._filter_version_compare,
            }
        )

        return env.get_template(file_name).render(
            item=data,
            nginx_acme=self.acme,
            nginx_version=self.nginx_version,
        )

    # ------------------------------------------------------------------
    # Private Jinja2 filter implementations
    # ------------------------------------------------------------------

    @staticmethod
    def _filter_var_type(value: Any) -> Optional[str]:
        """Return a string describing the Python type of *value*.

        Recognised types: ``"list"``, ``"dict"``, ``"string"``, ``"int"``,
        ``"boolean"``.  Returns ``None`` for all other types.

        Args:
            value: Any Jinja2 template value.

        Returns:
            Type name string or ``None``.
        """
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "int"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "list"
        if isinstance(value, dict):
            return "dict"
        return None

    @staticmethod
    def _filter_regex_replace(s: Any, find: str, replace: str) -> str:
        """Apply ``re.sub(find, replace, s)`` and strip surrounding whitespace.

        Args:
            s: Input value (coerced to string).
            find: Regular expression pattern.
            replace: Replacement string.

        Returns:
            Substituted and stripped string.
        """
        return re.sub(str(find), str(replace), str(s)).strip()

    @staticmethod
    def _filter_split(value: Any, sep: str = "") -> List[str]:
        """Split *value* on *sep*, discarding empty tokens.

        Args:
            value: Input value; splitting is only performed for strings.
            sep: Separator string.  Empty string splits on every character.

        Returns:
            List of non-empty string tokens, or an empty list when *value*
            is not a string.
        """
        if isinstance(value, str):
            return list(filter(None, value.split(sep)))
        return []

    @staticmethod
    def _filter_validate_listener(
        data: Any,
        regex: str = r"(quic|reuseport)",
        replace: str = "",
    ) -> List[str]:
        """Strip unsupported tokens from nginx ``listen`` directive values.

        Useful for removing ``quic`` or ``reuseport`` from listen strings
        on nginx versions that do not support them.

        Args:
            data: Either a single listen string or a list of listen strings.
            regex: Pattern identifying tokens to remove.
            replace: Replacement for matched tokens (default: remove).

        Returns:
            List of sanitised listen strings with surrounding whitespace
            stripped from each entry.
        """
        if isinstance(data, str):
            return [re.sub(regex, replace, data).strip()]
        if isinstance(data, list):
            return [re.sub(regex, replace, str(item)).strip() for item in data]
        return []

    @staticmethod
    def _filter_version_compare(
        value: str,
        version: str,
        compare_operator: str = "eq",
    ) -> bool:
        """Compare two semantic version strings.

        Wraps :class:`packaging.version.Version` to provide a Jinja2-callable
        version comparison filter.

        Args:
            value: Left-hand version string (e.g. ``"1.25.3"``).
            version: Right-hand version string to compare against.
            compare_operator: Comparison operator; one of ``==``, ``=``,
                ``eq``, ``<``, ``lt``, ``<=``, ``le``, ``>``, ``gt``,
                ``>=``, ``ge``, ``!=``, ``<>``, ``ne``.

        Returns:
            Boolean result of the comparison.

        Raises:
            ValueError: When *value* or *version* is empty, or when an
                unknown *compare_operator* is supplied.
            RuntimeError: When :mod:`packaging.version` raises during
                comparison.
        """
        if not value:
            raise ValueError("Input version value cannot be empty.")
        if not version:
            raise ValueError("Version parameter to compare against cannot be empty.")

        op_key = _OP_MAP.get(compare_operator)
        if op_key is None:
            valid = ", ".join(map(repr, _OP_MAP))
            raise ValueError(
                f"Invalid operator type ({compare_operator!r}). "
                f"Must be one of {valid}."
            )

        try:
            method = getattr(operator, op_key)
            return method(Version(to_text(value)), Version(to_text(version)))
        except Exception as exc:
            raise RuntimeError(f"Version comparison failed: {to_native(exc)}") from exc


# ===========================================================================
# Main module class
# ===========================================================================


class NginxVHosts:
    """Render, deploy, enable and disable nginx vhost configuration files.

    The class coordinates four concerns:

    1. Reading the nginx version from the local Ansible facts file.
    2. Delegating Jinja2 rendering to :class:`VhostTemplateRenderer`.
    3. Writing rendered content to ``sites-available`` when changed.
    4. Managing ``sites-enabled`` symlinks.

    Attributes:
        module: The :class:`AnsibleModule` instance provided by Ansible.
        vhosts: List of vhost configuration dicts.
        dest: Destination directory for rendered vhost files
            (normally ``/etc/nginx/sites-available``).
        acme: ACME configuration dict passed into the template context.
        ignore_missing_certificate: When ``True``, a missing TLS certificate
            causes a warning instead of a failure.
        default_http_template: Default template file name for HTTP vhosts.
        default_https_template: Default template file name for HTTPS vhosts.
        template_path: Absolute path to the template directory.
        site_enabled: Path to the ``sites-enabled`` directory.
        site_available: Path to the ``sites-available`` directory.
        tmp_directory: Per-PID working directory for temporary render output.
        nginx_version: Installed nginx version string; resolved in
            :meth:`run` from the local Ansible facts file.
        checksum: :class:`Checksum` helper for file-level change detection.
    """

    def __init__(self, module: AnsibleModule) -> None:
        """Initialise from Ansible module parameters.

        Args:
            module: Fully initialised :class:`AnsibleModule` instance.
        """
        self.module = module
        self.module.log("NginxVHosts::__init__()")

        self.vhosts: List[Dict[str, Any]] = module.params["vhosts"]
        self.dest: str = module.params.get("dest") or "/etc/nginx/sites-available"
        self.acme: Optional[Dict[str, Any]] = module.params.get("acme")
        self.ignore_missing_certificate: bool = module.params.get(
            "ignore_missing_certificate", False
        )

        template: Dict[str, Any] = module.params.get("template") or {}
        self.default_http_template: str = template.get("http", "")
        self.default_https_template: str = template.get("https", "")
        self.template_path: str = template.get("path", "")

        self.site_enabled: str = "/etc/nginx/sites-enabled"
        self.site_available: str = "/etc/nginx/sites-available"
        self.tmp_directory: str = os.path.join(_TMP_BASE, f"nginx_vhosts.{os.getpid()}")

        # Resolved at runtime after reading the nginx facts file.
        self.nginx_version: str = "0.0.0"
        self.checksum = Checksum(module)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """Execute the full vhost lifecycle for all configured vhosts.

        Sequence:

        1. Create the per-PID temporary directory.
        2. Read the nginx version from the local Ansible facts file.
        3. Instantiate :class:`VhostTemplateRenderer` with the resolved version.
        4. Iterate over ``vhosts``, calling :meth:`create_vhost` or
           :meth:`remove_vhost` as appropriate.
        5. Aggregate results and remove the temporary directory.

        Returns:
            Ansible result dict with keys ``changed``, ``failed``, ``msg``.
        """
        self.module.log("NginxVHosts::run()")

        create_directory(directory=self.tmp_directory, mode="0750")

        self.nginx_version = self._load_nginx_version()

        self._renderer = VhostTemplateRenderer(
            module=self.module,
            template_path=self.template_path,
            acme=self.acme,
            nginx_version=self.nginx_version,
        )

        result_state: List[Dict[str, Any]] = []

        for vhost in self.vhosts:
            name: str = vhost.get("name") or ""
            vhost_state: str = vhost.get("state", "present")

            res: Dict[str, Any] = {name: {}}

            if vhost_state == "absent":
                disabled, removed = self.remove_vhost(vhost)
                changed, msg = self._absent_message(disabled, removed)
                if changed:
                    res[name].update({"changed": changed, "msg": msg})
                    result_state.append(res)
            else:
                failed, changed, msg = self.create_vhost(vhost)
                res[name].update({"failed": failed, "changed": changed, "msg": msg})
                result_state.append(res)

        _state, _changed, _failed, state, changed, failed = results(
            self.module, result_state
        )

        shutil.rmtree(self.tmp_directory, ignore_errors=True)

        return dict(changed=_changed, failed=_failed, msg=result_state)

    # ------------------------------------------------------------------
    # Public vhost operations
    # ------------------------------------------------------------------

    def create_vhost(self, data: Dict[str, Any]) -> Tuple[bool, bool, str]:
        """Render, write, and optionally enable a single vhost.

        Template selection priority:

        1. Explicit ``template`` key in *data*.
        2. HTTPS default template when ``ssl.enabled`` is ``true``.
        3. HTTP default template otherwise.

        TLS guard:
            When ``ssl.enabled`` is ``true`` and ``ssl.state`` is
            ``"missing"``, the vhost activation is either skipped with a
            warning (``ignore_missing_certificate=True``) or fails hard.

        Args:
            data: Single vhost configuration dict.

        Returns:
            A 3-tuple ``(failed, changed, message)``.
        """
        self.module.log(f"NginxVHosts::create_vhost(data: {data})")

        enabled: bool = data.get("enabled", True)
        template_file: Optional[str] = data.get("template")
        tls: Optional[Dict[str, Any]] = data.get("ssl")

        # Resolve TLS state *before* template selection so the correct
        # default template is chosen when no explicit override is given.
        tls_enabled: bool = bool(tls and tls.get("enabled", False))

        if not template_file:
            template_file = (
                self.default_https_template
                if tls_enabled
                else self.default_http_template
            )

        template = os.path.join(self.template_path, template_file)

        if not os.path.exists(template):
            return True, False, f"The template '{template_file}' does not exist."

        file_available, file_enabled, file_temporary = self._file_names(data)

        vhost_content = self.render_template(template, data)

        if vhost_content is None:
            return True, False, f"Template '{template_file}' could not be rendered."

        changed, msg = self.save_vhost(file_available, file_temporary, vhost_content)

        if enabled:
            if tls_enabled and tls:
                tls_cert_state: str = tls.get("state", "missing")

                _failed = False
                _changed = False
                _msg = "The virtual host could not be activated because the TLS certificate is missing."

                if tls_cert_state == "missing":
                    if self.ignore_missing_certificate:
                        _msg = f"[WARNING] {_msg}"
                    else:
                        _failed = True
                        _msg = f"[ERROR] {_msg}"

                    return (_failed, _changed, _msg)
                    #     return (
                    #         False,
                    #         False,
                    #         "[WARNING] The virtual host could not be activated "
                    #         "because the TLS certificate is missing.",
                    #     )
                    # return (
                    #     True,
                    #     False,
                    #     "[ERROR] The virtual host could not be activated "
                    #     "because the TLS certificate is missing.",
                    # )

            symlink_changed = self.enable_vhost(file_available, file_enabled)
            if symlink_changed:
                if changed:
                    msg += " and enabled."
                else:
                    changed = True
                    msg = "The VHost was successfully enabled."
        else:
            symlink_changed = self.disable_vhost(file_enabled)
            if symlink_changed:
                if changed:
                    msg += " and disabled."
                else:
                    changed = True
                    msg = "The VHost was successfully disabled."

        return False, changed, msg

    def render_template(
        self,
        vhost_template: str,
        data: Dict[str, Any],
    ) -> Optional[str]:
        """Delegate rendering to the :class:`VhostTemplateRenderer`.

        This method is part of the public interface and preserves backward
        compatibility.  Internally it delegates to
        :attr:`_renderer`.

        Args:
            vhost_template: Absolute path to the Jinja2 template file.
            data: Per-vhost data dict passed as ``item`` into the template.

        Returns:
            Rendered template string, or ``None`` on failure.
        """
        return self._renderer.render(vhost_template, data)

    def remove_vhost(self, data: Dict[str, Any]) -> Tuple[bool, bool]:
        """Remove the symlink and source file for a vhost.

        Args:
            data: Single vhost configuration dict.

        Returns:
            A 2-tuple ``(disabled, removed)`` where *disabled* is ``True``
            when the ``sites-enabled`` symlink was removed and *removed* is
            ``True`` when the ``sites-available`` source file was deleted.
        """
        self.module.log(f"NginxVHosts::remove_vhost(data: {data})")

        disabled = False
        removed = False

        file_available, file_enabled, _ = self._file_names(data)

        # Disable: remove the symlink from sites-enabled.
        if os.path.islink(file_enabled):
            disabled = remove_file(file_enabled)

        # Remove: delete the source config file from sites-available.
        if os.path.isfile(file_available):
            removed = remove_file(file_available)

        return disabled, removed

    def save_vhost(
        self,
        file_name: str,
        file_temporary: str,
        data: str,
    ) -> Tuple[bool, str]:
        """Write rendered vhost content to *file_name* when changed.

        The rendered string is written to *file_temporary* first.  A
        checksum comparison against the existing *file_name* determines
        whether the file needs to be updated.  Only when checksums differ
        is *file_temporary* atomically moved to *file_name*.

        Args:
            file_name: Target path in ``sites-available``.
            file_temporary: Scratch path in the per-PID temp directory.
            data: Rendered vhost configuration string.

        Returns:
            A 2-tuple ``(changed, message)``.
        """
        self.module.log(
            f"NginxVHosts::save_vhost("
            f"file_name: {file_name}, file_temporary: {file_temporary})"
        )

        with open(file_temporary, "w") as fh:
            fh.write(data)

        old_checksum = self.checksum.checksum_from_file(file_name)
        new_checksum = self.checksum.checksum_from_file(file_temporary)

        if new_checksum == old_checksum:
            return False, "The VHost has not been changed."

        new_file = old_checksum is None
        shutil.move(file_temporary, file_name)

        if new_file:
            return True, "The VHost was successfully created."
        return True, "The VHost was successfully changed."

    def enable_vhost(self, file_available: str, file_enabled: str) -> bool:
        """Create a symlink in ``sites-enabled`` pointing to ``sites-available``.

        A valid, existing symlink is left untouched.  A stale symlink
        (wrong target) is replaced; a missing symlink is created.

        Args:
            file_available: Absolute path to the source file in
                ``sites-available``.
            file_enabled: Absolute path to the symlink in ``sites-enabled``.

        Returns:
            ``True`` when the symlink was created or replaced, ``False``
            when it was already correct (no change).
        """
        self.module.log(
            f"NginxVHosts::enable_vhost("
            f"file_available: {file_available}, file_enabled: {file_enabled})"
        )

        # Fast-path: symlink already correct.
        if os.path.islink(file_enabled) and os.readlink(file_enabled) == file_available:
            return False

        force = os.path.islink(file_enabled)
        if force:
            self.module.log(
                f"replacing stale symlink '{file_enabled}' → '{file_available}'"
            )

        create_link(file_available, file_enabled, force)
        return True

    def disable_vhost(self, file_enabled: str) -> bool:
        """Remove the symlink for a vhost from ``sites-enabled``.

        Args:
            file_enabled: Absolute path to the symlink in ``sites-enabled``.

        Returns:
            ``True`` when the symlink was removed, ``False`` when it did
            not exist (idempotent no-op).
        """
        self.module.log(f"NginxVHosts::disable_vhost(file_enabled: {file_enabled})")
        return remove_file(file_enabled)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_nginx_version(self) -> str:
        """Read the installed nginx version from the Ansible facts file.

        The facts file is expected to be an executable script that writes
        a JSON object to stdout.  The JSON object must contain a ``version``
        key.

        Returns:
            Version string (e.g. ``"1.25.3"``), or ``"0.0.0"`` when the
            facts file does not exist or cannot be parsed.
        """
        if not os.path.exists(_FACTS_FILE):
            return "0.0.0"

        rc, out, _err = self._exec([_FACTS_FILE])

        if rc != 0 or not out:
            return "0.0.0"

        try:
            facts: Dict[str, Any] = json.loads(out)
            return facts.get("version", "0.0.0")
        except json.JSONDecodeError:
            return "0.0.0"

    def _file_names(self, data: Dict[str, Any]) -> Tuple[str, str, str]:
        """Derive the three canonical file paths for a vhost.

        Args:
            data: Single vhost configuration dict.  Must contain at least
                a ``name`` key.  An optional ``filename`` key overrides the
                default ``<name>.conf`` naming.

        Returns:
            A 3-tuple ``(available_path, enabled_path, temporary_path)``
            where:

            * *available_path* – absolute path in ``sites-available``.
            * *enabled_path* – absolute path in ``sites-enabled``.
            * *temporary_path* – absolute path in the per-PID temp dir.
        """
        name: str = data.get("name") or ""
        file_name: str = data.get("filename") or f"{name}.conf"

        available = os.path.join(self.site_available, file_name)
        enabled = os.path.join(self.site_enabled, file_name)
        temporary = os.path.join(self.tmp_directory, file_name)

        return available, enabled, temporary

    def _exec(
        self,
        cmd: List[str],
        check: bool = False,
    ) -> Tuple[int, str, str]:
        """Execute an external command via the Ansible module helper.

        Args:
            cmd: Argv list to execute.
            check: When ``True`` Ansible raises on non-zero exit codes.

        Returns:
            A 3-tuple ``(rc, stdout, stderr)``.
        """
        rc, out, err = self.module.run_command(cmd, check_rc=check)

        if rc != 0:
            self.module.log(f"  rc : '{rc}'")
            self.module.log(f"  out: '{out}'")
            self.module.log(f"  err: '{err}'")

        return rc, out, err

    @staticmethod
    def _absent_message(disabled: bool, removed: bool) -> Tuple[bool, str]:
        """Derive a human-readable message from ``remove_vhost`` results.

        Args:
            disabled: Whether the ``sites-enabled`` symlink was removed.
            removed: Whether the ``sites-available`` source file was deleted.

        Returns:
            A 2-tuple ``(changed, message)``.
        """
        if disabled and removed:
            return True, "The VHost was successfully disabled and removed."
        if disabled:
            return True, "The VHost was successfully disabled."
        if removed:
            return True, "The VHost was successfully removed."
        return False, "The VHost was already absent."


# ---------------------------------------------------------------------------


def main() -> None:
    """Module entry point.  Called by Ansible at runtime."""
    args: Dict[str, Any] = dict(
        vhosts=dict(required=True, type="list", elements="dict"),
        template=dict(required=True, type="dict"),
        dest=dict(required=False, default="/etc/nginx/sites-available"),
        acme=dict(required=False, type="dict"),
        ignore_missing_certificate=dict(required=False, type="bool", default=False),
    )

    module = AnsibleModule(argument_spec=args, supports_check_mode=True)

    p = NginxVHosts(module)
    result = p.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


if __name__ == "__main__":
    main()
