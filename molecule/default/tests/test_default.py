
from __future__ import unicode_literals

from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar

import json
import pytest
import os

import testinfra.utils.ansible_runner

HOST = 'instance'

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts(HOST)


def pp_json(json_thing, sort=True, indents=2):
    if type(json_thing) is str:
        print(json.dumps(json.loads(json_thing), sort_keys=sort, indent=indents))
    else:
        print(json.dumps(json_thing, sort_keys=sort, indent=indents))
    return None


def base_directory():
    """ ... """
    cwd = os.getcwd()

    if('group_vars' in os.listdir(cwd)):
        directory = "../.."
        molecule_directory = "."
    else:
        directory = "."
        molecule_directory = "molecule/{}".format(os.environ.get('MOLECULE_SCENARIO_NAME'))

    return directory, molecule_directory


def read_ansible_yaml(file_name, role_name):
    ext_arr = ["yml", "yaml"]

    read_file = None

    for e in ext_arr:
        test_file = "{}.{}".format(file_name, e)
        if os.path.isfile(test_file):
            read_file = test_file
            break

    return "file={} name={}".format(read_file, role_name)


@pytest.fixture()
def get_vars(host):
    """
        parse ansible variables
        - defaults/main.yml
        - vars/main.yml
        - vars/${DISTRIBUTION}.yaml
        - molecule/${MOLECULE_SCENARIO_NAME}/group_vars/all/vars.yml
    """
    base_dir, molecule_dir = base_directory()
    distribution = host.system_info.distribution
    operation_system = None

    if distribution in ['debian', 'ubuntu']:
        operation_system = "debian"
    elif distribution in ['redhat', 'ol', 'centos', 'rocky', 'almalinux']:
        operation_system = "redhat"
    elif distribution in ['arch', 'artix']:
        operation_system = f"{distribution}linux"

    file_defaults = f"file={base_dir}/defaults/main.yaml name=role_defaults"
    file_vars = f"file={base_dir}/vars/main.yaml name=role_vars"
    file_molecule = f"file={molecule_dir}/group_vars/all/vars.yml name=test_vars"
    file_distibution = f"file={base_dir}/vars/{operation_system}.yaml name=role_distibution"

    defaults_vars      = host.ansible("include_vars", file_defaults).get("ansible_facts").get("role_defaults")
    vars_vars          = host.ansible("include_vars", file_vars).get("ansible_facts").get("role_vars")
    distibution_vars   = host.ansible("include_vars", file_distibution).get("ansible_facts").get("role_distibution")
    molecule_vars      = host.ansible("include_vars", file_molecule).get("ansible_facts").get("test_vars")
    # host_vars          = host.ansible("include_vars", file_host_molecule).get("ansible_facts").get("host_vars")

    ansible_vars = defaults_vars
    ansible_vars.update(vars_vars)
    ansible_vars.update(distibution_vars)
    ansible_vars.update(molecule_vars)
    # ansible_vars.update(host_vars)

    templar = Templar(loader=DataLoader(), variables=ansible_vars)
    result = templar.template(ansible_vars, fail_on_undefined=False)

    return result


def test_installed_package(host):
    distribution = host.system_info.distribution
    release = host.system_info.release

    print(f"distribution: {distribution}")
    print(f"release     : {release}")

    if not distribution == "artix":
        p = host.package("nginx")
        assert p.is_installed


@pytest.mark.parametrize("dirs", [
    "/etc/nginx/sites-available",
    "/etc/nginx/sites-enabled",
    "/etc/nginx/includes.d",
    "/etc/nginx/conf.d",
])
def test_directories(host, dirs):
    d = host.file(dirs)
    assert d.is_directory


@pytest.mark.parametrize("files", [
    "/etc/nginx/nginx.conf",
    "/etc/nginx/includes.d/nginx_log.conf",
    "/etc/nginx/conf.d/ssl.conf",
    "/etc/nginx/conf.d/gzip.conf",
])
def test_directories(host, files):
    d = host.file(files)
    assert d.is_file

def test_service(host):
    service = host.service("nginx")
    assert service.is_enabled
    assert service.is_running
