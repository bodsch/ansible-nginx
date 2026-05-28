# coding: utf-8
from __future__ import annotations, unicode_literals

import os

import pytest
import testinfra.utils.ansible_runner
from helper.molecule import get_vars, infra_hosts, local_facts

testinfra_hosts = infra_hosts(host_name="instance")

# --- tests -----------------------------------------------------------------

# _facts = local_facts(host=host, fact="nginx")


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


@pytest.mark.parametrize(
    "files",
    [
        "00-status.conf",
        "10-01.docker.local.conf",
        "10-02.docker.local.conf",
        "10-03.docker.local.conf",
        "10-04.docker.local.conf",
        "10-05.docker.local.conf",
        "10-06.docker.local.conf",
        "10-07.docker.local.conf",
        "10-08.docker.local.conf",
        "10-09.docker.local.conf",
        "10-10.docker.local.conf",
        "10-11.docker.local.conf",
        "10-12.docker.local.conf",
        "10-13.docker.local.conf",
        "10-14.docker.local.conf",
        "10-15.docker.local.conf",
        "10-16.docker.local.conf",
        "10-17.docker.local.conf",
        "10-18.docker.local.conf",
        "10-19.docker.local.conf",
        "10-20.docker.local.conf",
        "10-21.docker.local.conf",
        "10-22.docker.local.conf",
        "10-23.docker.local.conf",
        "10-24.docker.local.conf",
        "10-25.docker.local.conf",
        "20-molecule.docker.local.conf",
    ],
)
def test_vhosts_available(host, files):
    d = host.file(f"/etc/nginx/sites-available/{files}")
    assert d.is_file


@pytest.mark.parametrize(
    "files",
    [
        "00-status.conf",
        "10-01.docker.local.conf",
        "10-03.docker.local.conf",
        "10-04.docker.local.conf",
        "10-05.docker.local.conf",
        "10-06.docker.local.conf",
        "10-07.docker.local.conf",
        "10-08.docker.local.conf",
        "10-09.docker.local.conf",
        "10-10.docker.local.conf",
        "10-11.docker.local.conf",
        "10-12.docker.local.conf",
        "10-13.docker.local.conf",
        "10-14.docker.local.conf",
        "10-15.docker.local.conf",
        "10-16.docker.local.conf",
        "10-17.docker.local.conf",
        "10-18.docker.local.conf",
        "10-19.docker.local.conf",
        "10-20.docker.local.conf",
        "10-21.docker.local.conf",
        "10-22.docker.local.conf",
        "10-23.docker.local.conf",
        "10-24.docker.local.conf",
        "10-25.docker.local.conf",
        "20-molecule.docker.local.conf",
    ],
)
def test_vhosts_enabled(host, files):
    d = host.file(f"/etc/nginx/sites-enabled/{files}")
    assert d.is_file

@pytest.mark.parametrize(
    "directories",
    [
      "/var/www",
      "/var/www/01.docker.local",
      "/var/www/02.docker.local",
      "/var/www/03.docker.local",
      "/var/www/04.docker.local",
      "/var/www/05.docker.local",
      "/var/www/06.docker.local",
      "/var/www/07.docker.local",
      "/var/www/08.docker.local",
      "/var/www/09.docker.local",
      "/var/www/10.docker.local",
      "/var/www/11.docker.local",
      "/var/www/12.docker.local",
      "/var/www/13.docker.local",
      "/var/www/14.docker.local",
      "/var/www/15.docker.local",
      "/var/www/16.docker.local",
      "/var/www/17.docker.local",
      "/var/www/18.docker.local",
      "/var/www/19.docker.local",
      "/var/www/20.docker.local",
      "/var/www/21.docker.local",
      "/var/www/22.docker.local",
      "/var/www/23.docker.local",
      "/var/www/24.docker.local",
      "/var/www/25.docker.local",
      "/var/www/docker.local",
      "/var/www/foo.docker.local",
      "/var/www/foo.docker.local",
    ],
)
def test_vhosts_root_directories(host, directories):
    d = host.file(directories)
    assert d.is_directory


def test_service(host):
    service = host.service("nginx")
    assert service.is_enabled
    assert service.is_running
