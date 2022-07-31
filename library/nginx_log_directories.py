#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2021-2022, Bodo Schulz <bodo@boone-schulz.de>
# Apache (see LICENSE or https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function
import os
import pwd
import grp

from ansible.module_utils.basic import AnsibleModule


class NginxLogDirectories(object):
    """
    """

    def __init__(self, module):
        """
        """
        self.module = module

        self.vhosts = module.params.get("vhosts")
        self.owner = module.params.get("owner")
        self.group = module.params.get("group")
        self.mode = str(module.params.get("mode"))

    def run(self):
        """
        """
        log_dirs = []
        result_state = []

        for vhost, values in self.vhosts.items():
            # self.module.log(msg=f" - {vhost}")
            logfiles = values.get("logfiles", {})

            if logfiles:
                access_log = logfiles.get("access", {}).get("file", None)
                error_log = logfiles.get("error", {}).get("file", None)

                if access_log:
                    dirname = os.path.dirname(access_log)
                    log_dirs.append(dirname)

                if error_log:
                    dirname = os.path.dirname(error_log)
                    log_dirs.append(dirname)

        unique_dirs = list(dict.fromkeys(log_dirs))

        for d in unique_dirs:
            changed = False
            d_created = False
            d_ownership = False

            if not os.path.exists(d):
                d_created = self.__create_directory(d)

            d_ownership = self.__fix_ownership(d)

            if d_created or d_ownership:
                changed = True

            if changed:
                res = {}
                state = "directory successful created"

                res[d] = dict(
                    # changed=True,
                    state=state
                )

                result_state.append(res)

        # define changed for the running tasks
        # migrate a list of dict into dict
        combined_d = {key: value for d in result_state for key, value in d.items()}
        # find all changed and define our variable
        changed = (len({k: v for k, v in combined_d.items() if v.get('state')}) > 0)

        result = dict(
            changed = changed,
            failed = False,
            state = result_state
        )

        return result

    def __create_directory(self, dir):
        """
        """
        try:
            os.makedirs(dir, exist_ok=True)
        except FileExistsError:
            pass

        if os.path.isdir(dir):
            return True
        else:
            return False

    def __fix_ownership(self, dir):
        """
        """
        changed      = False
        force_owner  = self.owner
        force_group  = self.group
        force_mode   = self.mode

        if os.path.isdir(dir):
            current_owner, current_group, current_mode = self.__current_state(dir)

            # change mode
            if force_mode is not None and force_mode != current_mode:
                try:
                    if isinstance(force_mode, int):
                        mode = int(str(force_mode), base=8)
                except Exception as e:
                    self.module.log(msg=f" - ERROR '{e}'")

                try:
                    if isinstance(force_mode, str):
                        mode = int(force_mode, base=8)
                except Exception as e:
                    self.module.log(msg=f" - ERROR '{e}'")

                os.chmod(dir, mode)

            # change ownership
            if force_owner is not None or force_group is not None and (force_owner != current_owner or force_group != current_group):
                if force_owner is not None:
                    try:
                        force_owner = pwd.getpwnam(str(force_owner)).pw_uid
                    except KeyError:
                        force_owner = int(force_owner)
                        pass
                elif current_owner is not None:
                    force_owner = current_owner
                else:
                    force_owner = 0

                if force_group is not None:
                    try:
                        force_group = grp.getgrnam(str(force_group)).gr_gid
                    except KeyError:
                        force_group = int(force_group)
                        pass
                elif current_group is not None:
                    force_group = current_group
                else:
                    force_group = 0

                os.chown(
                    dir,
                    int(force_owner),
                    int(force_group)
                )

            _owner, _group, _mode = self.__current_state(dir)

            if (current_owner != _owner) or (current_group != _group) or (current_mode != _mode):
                changed = True

        return changed

    def __current_state(self, dir):
        """
        """
        if os.path.isdir(dir):
            _state = os.stat(dir)
            try:
                current_owner  = pwd.getpwuid(_state.st_uid).pw_uid
            except KeyError:
                pass

            try:
                current_group = grp.getgrgid(_state.st_gid).gr_gid
            except KeyError:
                pass

            try:
                current_mode  = oct(_state.st_mode)[-4:]
            except KeyError:
                pass

        return current_owner, current_group, current_mode

    def _permstr_to_octal(self, modestr, umask):
        '''
            Convert a Unix permission string (rw-r--r--) into a mode (0644)
        '''
        revstr = modestr[::-1]
        mode = 0
        for j in range(0, 3):
            for i in range(0, 3):
                if revstr[i + 3 * j] in ['r', 'w', 'x', 's', 't']:
                    mode += 2 ** (i + 3 * j)

        return (mode & ~umask)


# ===========================================
# Module execution.


def main():

    module = AnsibleModule(

        argument_spec=dict(
            vhosts=dict(
                required=True,
                type="dict"
            ),
            owner=dict(
                required=False,
                type="str"
            ),
            group=dict(
                required=False,
                type="str"
            ),
            mode=dict(
                required=False,
                type="raw",
                default="0755"
            )
        ),
        supports_check_mode=True,
    )

    p = NginxLogDirectories(module)
    result = p.run()

    # module.log(msg="= result: {}".format(result))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
