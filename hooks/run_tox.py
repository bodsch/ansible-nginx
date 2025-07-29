#!/usr/bin/python3

import os
import sys
import argparse
import subprocess
import yaml
import shutil
import logging
import atexit
import signal
from pathlib import Path
from typing import Optional, List
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

VERSION = "2.1.1"


@contextmanager
def chdir(path: Path):
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


def read_galaxy_namespace(cwd: Path) -> Optional[str]:
    galaxy_file = cwd / 'galaxy.yml'
    if galaxy_file.exists():
        try:
            with galaxy_file.open('r') as f:
                data = yaml.safe_load(f)
            ns = data.get('namespace')
            name = data.get('name')
            if ns and name:
                return f"{ns}.{name}"

        except Exception as e:
            logging.warning(f"Could not parse galaxy.yml: {e}")

    return None


def read_collections_file(path: Path) -> List[str]:
    """
    Reads a collections.yml file and returns the list of collections defined.
    """
    try:
        with path.open('r') as f:
            data = yaml.safe_load(f)
        # assume top-level key 'collections' with list of names
        return data.get('collections', [])
    except Exception as e:
        logging.warning(f"Failed to read {path}: {e}")
        return []


def read_yaml(path: Path) -> Optional[dict]:
    """
    Safe-load a YAML file and return its contents as a dict, or None on failure.
    """
    try:
        with path.open('r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.warning(f"Could not read YAML {path}: {e}")
        return None


def gather_collections_files(root: Path, scenario: str) -> List[Path]:
    """
    Collects paths to collection definition files in the following order:
      1. root/galaxy.yml
      2. roles/<role>/collections.yml
      3. roles/<role>/molecule/<scenario>/collections.yml
    Returns only existing files.
    """
    files: List[Path] = []
    # 1. root galaxy.yml
    g = root / 'collections.yml'
    if g.exists():
        files.append(g)

    # 3. scenario-level collections.yml
    if scenario:
        scenario_file = root / 'molecule' / scenario / 'collections.yml'
        if scenario_file.exists():
            files.append(scenario_file)

    return files


class ToxRunner:
    """
    Executes tox and related build tasks for Ansible collections.
    Only runs management and tests for the specified role and scenario.
    """

    required_env_vars = [
        'TOX_ANSIBLE',
        'TOX_SCENARIO',
    ]

    def __init__(self, tox_test: Optional[str] = None):
        """
        """
        self.cwd = Path.cwd()
        self.roles_dir = self.cwd
        self.hooks_dir = self.cwd / "hooks"
        self.role = os.environ.get('ROLE', '').strip()
        self.scenario = os.environ.get('TOX_SCENARIO', 'default').strip()
        self.tox_test = tox_test or os.environ.get('TOX_TEST', '').strip()
        self.tox_silence = os.environ.get('TOX_SILENCE', "true").lower() in ("1", "true", "yes", "on")

        logger.debug(f"{self.tox_silence} - {type(self.tox_silence)}")

        self.home = Path.home()
        self.roles_path = self.home / ".ansible" / "roles"
        self.cwd = Path.cwd()
        self.role_base_name = self.cwd.name
        self.namespace = None
        self.name = None
        self.symlinks = []

        self.roles_path.mkdir(parents=True, exist_ok=True)
        self._setup_signal_handlers()
        self._link_role()
        self._parse_meta_and_link()

        sys.path.insert(0, str(self.hooks_dir))

    def _exit_hook(self):
        logger.debug(f"trap signal {self.rc}")
        logger.debug(self.symlinks)
        for link in self.symlinks:
            if link.exists() and link.is_symlink():
                link.unlink()

    def _setup_signal_handlers(self):
        def handler(signum, frame):
            self.rc = 1  # default error code for signals
            self._exit_hook()
            sys.exit(self.rc)

        for sig in [signal.SIGHUP, signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, handler)

        atexit.register(self._exit_hook)
        self.rc = 0

    def run(self) -> None:
        """
        """
        self.validate()
        self.collections()

        self._run_for_role()

        sys.exit(0)

    def validate(self) -> None:
        """
        """
        missing_vars = [v for v in self.required_env_vars if not os.getenv(v)]
        if missing_vars:
            logging.info("needed environment Variables:")
            filtered_env = {k: v for k, v in os.environ.items() if k.startswith(
                "TOX_") or k.startswith("COLLECTION_")}
            for key, value in filtered_env.items():
                logging.debug(f"{key}={value}")

            error = f"Missing environment variables: {', '.join(missing_vars)}"
            logging.error(error)
            sys.exit(1)

        # if not self.role:
        #     logging.error(
        #         "please set the COLLECTION_ROLE Environment Variable!\n")
        #     sys.exit(1)

    def collections(self) -> None:
        """ """
        logging.debug(
            f"Gathering collections for scenario='{self.scenario}'")
        collection_paths = gather_collections_files(
            self.cwd, self.scenario)

        if collection_paths:
            self._invoke_manage_collections(collection_paths)

    def _invoke_manage_collections(self, collections_files: List[Path]) -> None:
        """
        Imports and runs the AnsibleCollectionManager with the given collections files.
        """
        # print(f"ToxRunner::_invoke_manage_collections({collections_files})")

        try:
            import manage_collections
        except ImportError:
            logging.error(
                "Could not import manage_collections. Check hooks module path.")
            return

        print("")
        logging.info("Install dependencies:")
        logging.debug(
            f" Installing collections from files: {[str(p) for p in collections_files]}")
        try:
            manager = manage_collections.AnsibleCollectionManager(
                directory=str(self.cwd))

            required = []

            for f in collections_files:
                if f.name == "galaxy.yml":
                    required += manager.load_collection_dependencies()
                else:
                    required += manager.load_required_collections(path=f)
            manager.run(required)
        except Exception as e:
            logging.error(f"manage_collections failed: {e}")

    def _run_for_role(self, role_name: str = None) -> None:
        """
        """
        # print(f"ToxRunner::_run_for_role({role_name})")

        role_path = self.roles_dir
        if not role_path.exists():
            logging.error(f"Role path not found: {role_path}")
            return

        # self._copy_configs(role_path)

        if self.tox_test in ["converge", "destroy", "test", "verify"]:
            """
            """
            logging.info(
                f"Running for role {self.role} and scenario {self.scenario}\n")
            # env = self.filtered_env
            env = os.environ.copy()
            with chdir(role_path):
                local_tox_file = Path.cwd() / "tox.ini"
                local_requirements_file = Path.cwd() / "test-requirements.txt"

                if local_tox_file.exists() and local_requirements_file.exists():
                    # print(f"[INFO] tox default scenario at {role_path}")
                    self._run_tox(role_path, env)
                else:
                    logger.error("missing tox.ini or test-requirements.txt")

            # self._remove_configs(role_path)

            return

        logging.warning(f"unkown tox test {self.tox_test}")

    def _copy_configs(self, role_path: Path) -> None:
        """
        """
        logging.debug(f"ToxRunner::_copy_configs({role_path})")

        for fname in ['requirements.txt', 'test-requirements.txt', 'tox.ini']:
            src = self.cwd / fname

            logging.debug(f"  - {src}")
            if src.exists():
                try:
                    shutil.copy(src, role_path / fname)
                    logging.debug(f"Copied {fname} to {role_path}")
                except IOError as e:
                    logging.warning(f"Could not copy {fname}: {e}")
            else:
                logging.warning(f"missing: {src}")

    def _remove_configs(self, role_path: Path) -> None:
        """
        """
        print(f"ToxRunner::_remove_configs({role_path})")

        for fname in ['requirements.txt', 'test-requirements.txt', 'tox.ini']:
            dst = role_path / fname
            if dst.is_file():
                try:
                    dst.unlink()
                    logger.debug(f"Removed {dst}")
                except OSError as e:
                    logger.warning(f"Could not remove {fname}: {e}")

    def _run_tox(self, cwd: Path, env: dict) -> None:
        """
        """
        scenario = env.get("COLLECTION_SCENARIO", None)

        cmd = ['tox']
        cmd += [f'-e {env.get("TOX_ANSIBLE", "ansible_9.5")}']
        cmd += ['--', 'molecule']
        cmd += ([self.tox_test] if self.tox_test else [])

        if scenario:
            cmd += ["--scenario-name", scenario]

        cmd_str = ' '.join(cmd)

        logger.debug(cmd_str)

        try:
            logging.info(f"run tox: {cmd_str}")

            subprocess.run(
                cmd,
                cwd=str(cwd),
                env=env,
                capture_output=self.tox_silence,
                text=True,
                check=True
            )
            print("")
        except subprocess.CalledProcessError as e:
            """
            """
            logging.error(f"tox failed in {cwd}")
            logging.error("Command:")
            logging.error(f"  {cmd_str}")
            print("")
            logging.error('   STDOUT:')
            logging.error(f"  {e.stdout.strip()}")
            print("")
            logging.error('   STDERR:')
            logging.error(f"  {e.stderr.strip()}")
            print("")

            sys.exit(1)

        logging.info("successfuly.")

    def _link_role(self):
        """
        """
        link_name = self.roles_path / self.role_base_name
        self._safe_symlink(self.cwd, link_name)

    def _safe_symlink(self, target: Path, link_name: Path):
        """
        """
        if link_name.exists() or link_name.is_symlink():
            link_name.unlink()
        link_name.symlink_to(target, target_is_directory=True)
        self.symlinks.append(link_name)

    def _parse_meta_and_link(self):
        """
        """
        meta_path = self.cwd / "meta" / "main.yml"

        if meta_path.exists():
            with open(meta_path, 'r') as f:
                data = yaml.safe_load(f)

            self.name = data.get("galaxy_info", {}).get('role_name')
            self.namespace = data.get("galaxy_info", {}).get('namespace')

            if self.name and self.namespace:
                # logger.info(f"\nansible role: {self.namespace}.{self.name}")
                link_name = self.roles_path / f"{self.namespace}.{self.name}"

                self._safe_symlink(self.cwd, link_name)

                # set role_name
                self.role = f"{self.namespace}.{self.name}"


if __name__ == "__main__":
    """
    """
    parser = argparse.ArgumentParser(
        description=f"Run tox for Ansible collection with Molecule (Version: {VERSION})"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
        help="Show the program's version number and exit."
    )
    parser.add_argument(
        "tox_test",
        nargs="?",
        help="Tox test command to run (e.g., lint, test).",
    )
    args = parser.parse_args()

    runner = ToxRunner(tox_test=args.tox_test)
    runner.run()
