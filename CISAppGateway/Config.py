#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Global configuration for CISAppGateway.
"""

import os
import re
try:
    import json
except:
    import simplejson as json

from logging import \
    debug, log

VERBOSE = 5


class Config(dict):
    """
    Class responsible for configuration storage and initialization.

    Config stores variables as instace members e.g.:

        conf.config_file

    The variables are also accessible via dictionary interface e.g.:

        conf['conf_file']
    """

    def __init__(self, *args, **kwargs):
        """
        Upon initialisation some default values are applied to the variables.
        However to finish the initialization :py:meth:`Config.load` method
        should be called.
        """
        # Config is a dict. Make all the keys accessible as attributes while
        # retaining the dict API
        super(Config, self).__init__(*args, **kwargs)
        self.__dict__ = self

        # Define default values
        self.config_file = None  #: Config file name
        self.log_level = 'INFO'  #: Logging level
        self.log_output = None  #: Log output file name
        #: Valid job states as well as names of directories on shared storage
        #: that are used to monitor job states
        self.service_states = (
            'waiting', 'queued', 'running', 'closing', 'cleanup',
            'done', 'failed', 'aborted', 'killed',
        )
        #: Supported services
        self.allowed_services = ('Test', 'MultiNest', 'EPRCore')
        #: URL where output files are accessible to users
        self.gate_url_output = 'http://localhost:8000/'
        #: Path to the shared storage used as communication medium with
        #: AppServer
        self.gate_path_shared = 'Shared'
        #: Path where jobs output will be stored
        self.gate_path_output = 'Output'
        self.gate_path_jobs = None
        self.gate_path_exit = None
        self.gate_path_flags = None
        self.gate_path_waiting = None
        self.gate_path_queued = None
        self.gate_path_running = None
        self.gate_path_closing = None
        self.gate_path_cleanup = None
        self.gate_path_done = None
        self.gate_path_failed = None
        self.gate_path_aborted = None
        self.gate_path_killed = None
        self.gate_path_flag_delete = None
        self.gate_path_flag_stop = None
        self.gate_path_flag_old_api = None
        self.gate_path = {
            "waiting": None,
            "queued": None,
            "running": None,
            "closing": None,
            "cleanup": None,
            "done": None,
            "failed": None,
            "aborted": None,
            "killed": None,
        }

    def load(self, conf_name=None):
        """
        Load CISAppGateway configuration from JSON file and finalize the
        initialisation.

        :param conf_name: name of CISAppGateway config file. When *None* is
            provided hardcoded defaults are used.
        """

        if conf_name is not None:
            # Load configuration from option file
            debug("@Config - Loading global configuration: %s" % conf_name)
            self.config_file = conf_name
            with open(self.config_file) as _conf_file:
                _conf = self.json_load(_conf_file)
            log(VERBOSE, json.dumps(_conf))
            self.update(_conf)

        debug('@Config - Finalise configuration initialisation')
        # Normalize paths to full versions
        for _key, _value in self.items():
            if '_path_' in _key and isinstance(_value, (str, unicode)):
                log(VERBOSE,'@Config - Correct path to full one: %s -> %s.' %
                      (_key, _value))
                self[_key] = os.path.realpath(_value)

        # Generate subdir names
        self.gate_path_jobs = os.path.join(self.gate_path_shared, 'jobs')
        self.gate_path_exit = os.path.join(self.gate_path_shared, 'exit')
        self.gate_path_flags = os.path.join(self.gate_path_shared, 'flags')
        self.gate_path_waiting = os.path.join(self.gate_path_shared, 'waiting')
        self.gate_path_queued = os.path.join(self.gate_path_shared, 'queued')
        self.gate_path_running = os.path.join(self.gate_path_shared, 'running')
        self.gate_path_closing = os.path.join(self.gate_path_shared, 'closing')
        self.gate_path_cleanup = os.path.join(self.gate_path_shared, 'cleanup')
        self.gate_path_done = os.path.join(self.gate_path_shared, 'done')
        self.gate_path_failed = os.path.join(self.gate_path_shared, 'failed')
        self.gate_path_aborted = os.path.join(self.gate_path_shared, 'aborted')
        self.gate_path_killed = os.path.join(self.gate_path_shared, 'killed')
        self.gate_path_flag_delete = os.path.join(self.gate_path_flags, 'delete')
        self.gate_path_flag_stop = os.path.join(self.gate_path_flags, 'stop')
        self.gate_path_flag_old_api = os.path.join(self.gate_path_flags, 'old_api')
        self.gate_path = {
            "waiting": self.gate_path_waiting,
            "queued": self.gate_path_queued,
            "running": self.gate_path_running,
            "closing": self.gate_path_closing,
            "cleanup": self.gate_path_cleanup,
            "done": self.gate_path_done,
            "failed": self.gate_path_failed,
            "aborted": self.gate_path_aborted,
            "killed": self.gate_path_killed,
        }

        log(VERBOSE, self)

    def json_load(self, file):
        """
        Parse a JSON file

        First remove comments and then use the json module package
        Comments look like ::

                // ...
            or
                /*
                ...
                */

        Based on:
        http://www.lifl.fr/~riquetd/parse-a-json-file-with-comments.html.
        Much faster than https://github.com/getify/JSON.minify and
        https://gist.github.com/WizKid/1170297

        :param file: name of the file to parse.
        """
        content = ''.join(file.readlines())

        # Regular expression for comment
        comment_re = re.compile(
            '(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
            re.DOTALL | re.MULTILINE
        )

        ## Looking for comments
        match = comment_re.search(content)
        while match:
            # single line comment
            content = content[:match.start()] + content[match.end():]
            match = comment_re.search(content)

        # Return json file
        return json.loads(content)


#: Global Config class instance. Use it to access the CISAppGateway
#: configuration.
conf = Config()
