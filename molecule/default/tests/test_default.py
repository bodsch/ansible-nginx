# coding: utf-8
from __future__ import annotations, unicode_literals

import os

import pytest
import testinfra.utils.ansible_runner
from helper.molecule import get_vars, infra_hosts, local_facts

testinfra_hosts = infra_hosts(host_name="instance")

# --- tests -----------------------------------------------------------------

# _facts = local_facts(host=host, fact="nginx")

def is_safe_path(path):
    """
    """
    if not isinstance(path, str) or not path:
        return False

    if not os.path.isabs(path):
        return False

    # Relative Segmente wie ".." normalisieren
    path = os.path.normpath(path)

    if path == "/":
        return False

    protected_paths = [
        "/",
        "/bin",
        "/boot",
        "/dev",
        "/etc",
        "/home",
        "/lib",
        "/lib64",
        "/media",
        "/mnt",
        "/opt",
        "/proc",
        "/root",
        "/run",
        "/sbin",
        "/srv",
        "/sys",
        "/usr",
        "/var",
    ]

    for protected_path in protected_paths:
        protected_path = os.path.normpath(protected_path)

        # Geschützte Verzeichnisse selbst und ihre Eltern blockieren
        if (
            path == protected_path
            or protected_path.startswith(path.rstrip("/") + "/")
        ):
            return False

    return True


def test_installed_package(host):
    distribution = host.system_info.distribution
    release = host.system_info.release

    print(f"distribution: {distribution}")
    print(f"release     : {release}")

    if not distribution == "artix":
        p = host.package("nginx")
        assert p.is_installed


@pytest.mark.parametrize(
    "dirs",
    [
        "/etc/nginx/sites-available",
        "/etc/nginx/sites-enabled",
        "/etc/nginx/includes.d",
        "/etc/nginx/conf.d",
    ],
)
def test_directories(host, dirs):
    d = host.file(dirs)
    assert d.is_directory


def test_acme_directory(host, get_vars):

    acme = get_vars.get("nginx_acme", {})
    acme_defaults = get_vars.get("nginx_defaults_acme", {})



    acme_merged = acme_defaults | acme
    basepath: str | None = None

    print(acme)
    print(acme_defaults)
    print(acme_merged)

    enabled = acme_merged.get("enabled", False)

    if enabled:
        challenge_directory = acme_merged.get('challenge_directory', None)

        if challenge_directory:
            basepath = os.path.dirname(challenge_directory)

        user = get_vars.get("nginx_user")
        group = get_vars.get("nginx_group")

        if basepath and is_safe_path(basepath):
            d = host.file(basepath)
            assert d.is_directory
            assert d.user == user
            assert d.group == group
            assert d.mode == 0o775

        d = host.file(challenge_directory)
        assert d.is_directory
        assert d.user == user
        assert d.group == group
        assert d.mode == 0o775

@pytest.mark.parametrize(
    "files",
    [
        "/etc/nginx/nginx.conf",
        "/etc/nginx/includes.d/nginx_log.conf",
        "/etc/nginx/includes.d/ssl.conf",
        "/etc/nginx/includes.d/ssl_default.conf",
        "/etc/nginx/conf.d/gzip.conf",
    ],
)
def test_files(host, files):
    d = host.file(files)
    assert d.is_file


def test_service(host):
    service = host.service("nginx")
    assert service.is_enabled
    assert service.is_running
