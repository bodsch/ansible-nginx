#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2021-2022, Bodo Schulz <bodo@boone-schulz.de>
# Apache (see LICENSE or https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function
import os

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results
from ansible_collections.bodsch.core.plugins.module_utils.directory import create_directory, fix_ownership


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
        unique_dirs = []

        if isinstance(self.vhosts, dict):
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

        elif isinstance(self.vhosts, list):
            logfiles = [x for x in self.vhosts if x.get("logfiles", {})]

            access_logs = [x.get("logfiles").get("access", {}) for x in logfiles]
            access_log = [os.path.dirname(x.get("file")) for x in access_logs if x.get("file")]
            error_logs = [x.get("logfiles").get("error", {}) for x in logfiles]
            error_log  = [os.path.dirname(x.get("file")) for x in error_logs if x.get("file")]
            # self.module.log(msg=f" access log: {access_log}")
            # self.module.log(msg=f" error log : {error_log}")
            unique_dirs = list(set(access_log + error_log))

        for d in unique_dirs:
            changed = False
            d_created = False
            d_ownership = False

            if not os.path.exists(d):
                d_created = create_directory(d)

            d_ownership, error_msg = fix_ownership(d, self.owner, self.group, self.mode)

            if d_created or d_ownership:
                changed = True

            if changed:
                res = {}
                state = "directory successful created"

                res[d] = dict(
                    state=state
                )

                result_state.append(res)

        # define changed for the running tasks
        _state, _changed, _failed, state, changed, failed = results(self.module, result_state)

        result = dict(
            changed = _changed,
            failed = False,
            state = result_state
        )

        return result

        # # define changed for the running tasks
        # # migrate a list of dict into dict
        # combined_d = {key: value for d in result_state for key, value in d.items()}
        # # find all changed and define our variable
        # changed = (len({k: v for k, v in combined_d.items() if v.get('state')}) > 0)
        #
        # result = dict(
        #     changed = changed,
        #     failed = False,
        #     state = result_state
        # )
        #
        # return result


# ===========================================
# Module execution.


def main():

    args = dict(
        vhosts=dict(
            required=True,
            type="raw"
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
    )

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True,
    )

    p = NginxLogDirectories(module)
    result = p.run()

    # module.log(msg="= result: {}".format(result))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
