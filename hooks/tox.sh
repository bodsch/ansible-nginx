#!/usr/bin/env bash

. hooks/molecule.rc

TOX_TEST="${1}"

set -x

if [ -f "./requirements.yml" ]
then
  collections_installed=$(ansible-galaxy collection list | grep -c bodsch.core)
  # ansible-galaxy collection list | grep bodsch
  # /home/bodsch/.ansible/collections/ansible_collections
  # bodsch.core        1.0.2:
  # ansible-galaxy collection install --requirements-file ./requirements.old
fi

# if [ ! -z "${TOX_COLLECTION_ROLE}" ]
# then
#   if [ -d "roles/${TOX_COLLECTION_ROLE}" ]
#   then
#     echo "- ${TOX_COLLECTION_ROLE} - ${TOX_COLLECTION_SCENARIO}"
#
#     pushd "roles/${TOX_COLLECTION_ROLE}"
#
#     tox "${TOX_OPTS}" -- molecule ${TOX_TEST} --scenario-name ${TOX_COLLECTION_SCENARIO}
#
#     popd
#   else
#     echo "collection role ${TOX_COLLECTION_ROLE} not found."
#   fi
# else
#   for role in $(find roles -maxdepth 1 -mindepth 1 -type d -printf "%f\n")
#   do
#     pushd roles/$role
#
#     if [ -f "./tox.ini" ]
#     then
#       for test in $(find molecule -maxdepth 1 -mindepth 1 -type d -printf "%f\n")
#       do
#         export TOX_SCENARIO=$test
#
#         tox ${TOX_OPTS} -- molecule ${TOX_TEST} ${TOX_ARGS}
#       done
#     fi
#     popd
#   done
# fi

tox ${TOX_OPTS} -- molecule ${TOX_TEST} ${TOX_ARGS}
