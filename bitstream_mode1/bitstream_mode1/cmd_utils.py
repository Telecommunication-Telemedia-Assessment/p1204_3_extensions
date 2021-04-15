"""
Command-line helper utils

Author: Werner Robitza, Steve Göring
"""

import subprocess
import logging
import sys
from multiprocessing import Pool
from subprocess import SubprocessError

logger = logging.getLogger('main')


def shell_call(cmd, raw=True):
    """
    Run a command and return output of (returncode, stdout, sterr)  as result.

    Arguments:
        - cmd: string or list of command parts in case of raw=False
        - raw: if true, interpret string as raw command
    """
    try:
        x = subprocess.run(cmd, shell=raw, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ret = (x.returncode, str(x.stdout, "utf-8"), str(x.stderr, "utf-8"))
        return ret
    except SubprocessError as e:
        logger.error("System error running command: " + str(cmd))
        logger.error(str(e.output))
        sys.exit(1)


class ParallelRunner():
    """
    Class for running commands in parallel and getting output
    """
    def __init__(self, max_parallel=4):
        self.cmds = set()
        self.max_parallel = max_parallel
        self.outputs = {}

    def log_commands(self):
        for c in self.cmds:
            logger.info(c[0])

    def add_cmd(self, cmd, name=""):
        """
        Add a command to be processed in parallel.
        "name" is an optional short name given to the command which will be printed to output
        """
        if cmd:
            self.cmds.add((cmd, name))

    def _run_single_cmd(self, cmd, name):
        logger.info("starting command: {}".format(name))
        logger.debug("starting command: {}".format(cmd))
        ret, stdout, stderr = shell_call(cmd)
        if ret != 0:
            logger.error("Error running parallel command: {cmd} \n{stdout}\n{stderr}".format(cmd=cmd, stdout=stdout, stderr=stderr))
        return ret == 0
        self.outputs[cmd] = {
            "stdout": stdout,
            "stderr": stderr
        }

    def run_commands(self):
        logger.debug("starting parallel run of commands")
        pool = Pool(processes=self.max_parallel)
        results = pool.starmap(self._run_single_cmd, self.cmds)
        if not all(results):
            logger.error("There were errors in your commands. Please check the output and re-run the processing chain!")
            sys.exit(1)
        logger.debug("all processes completed")
        self.cmds = set()

    def num_commands(self):
        return len(self.cmds)

    def return_command_list(self):
        commandlist = []
        for c in self.cmds:
            commandlist.append(c[0])
        return commandlist


def run_command(cmd, name=""):
    """
    Run a command directly.
    "name" is an optional name given to the command, will be printed to info log.
    """

    # if name:
    #     logger.info("starting command: {}".format(name))
    logger.debug("starting command: {}".format(cmd))

    if cmd:
        ret, out, err = shell_call(cmd)
    else:
        return(0, 0)

    if ret == 0:
        return (out, err)
    else:
        logger.error("Error running command: {cmd}\nstdout: {out}\nstderr: {err}".format(cmd=cmd, out=out, err=err))
        sys.exit(1)
