"""
Functions used to interact with CISAppServer. The communication is implemented
using shared file system.
"""

import os
import tempfile
import uuid
import stat
import logging

try:
    import json
except:
    import simplejson as json

from logging import debug, error, warning
from string import capitalize

from CISAppGateway.Config import conf

logging.basicConfig(level=logging.DEBUG)


def submit(request):
    """
    Submit a job request to the processing queue.

    Creates a file with job description in JSON format. File name is unique and
    serves as job ID. The job is added to the queue for execution.

    :param request: dict with requests' attributes. A "service" attribute with
        valid value is required.  Other atributes will be passed to the
        execution script and input files by AppServer after validation.
    :return: Job ID
    """
    debug('Request %s' % json.dumps(request))
    # Request is required to define service keyword
    if 'service' not in request.keys():
        return 'Error: Missing service name'
    debug('Service defined: %s' % request['service'])

    # Only request for supported services are processed
    if request['service'] not in conf.allowed_services:
        return 'Error: Unsupported service'
    debug("Service selected: %s" % request['service'])

    try:
        # Create file to store the input data
        # The file name is unique and will be used as request ID
        # Add UUID into the mix to allow for more then ~250k concurent ids
        prefix = request['service'] + '_' + str(uuid.uuid4()) + '_'
        (fd, name) = tempfile.mkstemp(prefix=prefix, dir=conf.gate_path_jobs)
        f = os.fdopen(fd, 'w')
        debug("Job ID file created")
        # Dump input data in JSON format (handle utf8 characters)
        f.write(json.dumps(request, ensure_ascii=False).encode('utf-8'))
        f.close()
        # Workaround until webserver an jobmanager run as same user
        _st = os.stat(name)
        os.chmod(name, _st.st_mode | stat.S_IRGRP | stat.S_IWGRP |
                 stat.S_IROTH | stat.S_IWOTH)
        debug("Job request data written to Job ID file")
        # Mark request as queued
        os.symlink(
            name,
            os.path.join(conf.gate_path_waiting, os.path.basename(name))
        )
    except Exception as e:
        return "Error: Exception cought while creating job request: %s" % e

    debug("Return request id: %s" % os.path.basename(name))
    return os.path.basename(name)


def status(id):
    """
    Check the status of a job.

    :param id: Job id to check
    :return: Job status [Waiting, Queued, Running, Done, Failed, Killed,
        Aborted]. For Done, Failed and Aborted states additional info is
        provided after ":". Returns Error string if id does not exist.
    """
    # Check if the job exists (file with it's id should be present in jobs
    # subdir)
    debug("@status - Status check for job: %s" % id)
    if not os.path.isfile(os.path.join(conf.gate_path_jobs, id)):
        warning("@status - Job ID not found")
        return "Error: Job with ID:%s not found" % id

    try:
        # Hide jobs scheduled for removal
        if os.path.exists(os.path.join(conf.gate_path_removed, id)):
            debug("Job marked for removal")
            return "Error: Job with ID:%s not found" % id
        # Handle remaining states
        elif os.path.exists(os.path.join(conf.gate_path_aborted, id)):
            _state = 'aborted'
        elif os.path.exists(os.path.join(conf.gate_path_failed, id)):
            _state = 'failed'
        elif os.path.exists(os.path.join(conf.gate_path_done, id)):
            _state = 'done'
        elif os.path.exists(os.path.join(conf.gate_path_killed, id)):
            _state = 'killed'
        elif os.path.exists(os.path.join(conf.gate_path_running, id)):
            _state = 'running'
        elif os.path.exists(os.path.join(conf.gate_path_queued, id)):
            _state = 'queued'
        elif os.path.exists(os.path.join(conf.gate_path_waiting, id)):
            _state = 'waiting'
        else:
            error("@status - Job status missing")
            return "Error: Job with ID:%s not found" % id
    except:
        error("@status - Unable to check job status", exc_info=True)
        return "Error: Unable to check job status"

    if _state in ('aborted', 'failed', 'done'):
        try:
            with open(os.path.join(conf.gate_path_exit, id)) as _status_file:
                return "".join(_status_file.readlines())
        except:
            error("@status - Unable to read job exit code", exc_info=True)
            return "Error: Unable to extract job exit code"
    else:
        debug("Job %s" % _state)
        return capitalize(_state)


def output(id):
    """
    Return base URL for output files for job identified by id.

    :return: URL. Returns Error string if id does not exist or job is not
        finished.
    """
    # Check if the job exists (file with it's id should be present in jobs
    # subdir)
    debug('@output - Output URL request')
    if not os.path.isfile(os.path.join(conf.gate_path_jobs, id)):
        warning("@output - Job ID not found")
        return "Error: Job with ID:%s not found" % id

    if os.path.exists(os.path.join(conf.gate_path_removed, id)):
        debug("@output - Job marked for removal")
        return "Error: Job with ID:%s not found" % id

    if not os.path.exists(os.path.join(conf.gate_path_done, id)) and \
       not os.path.exists(os.path.join(conf.gate_path_aborted, id)) and \
       not os.path.exists(os.path.join(conf.gate_path_failed, id)):
        return "Error: Job with ID:%s did not finish." % id

    return conf.gate_url_output + id


def delete(id):
    """
    Mark job idendified with id for deletion.

    The actual job removal along with related files is perfromed by job manager
    service.

    :param id: ID of job to be removed
    """

    # Check if the job exists (file with it's id should be present in jobs
    # subdir)
    debug("@delete - Job remove request %s" % id)
    if not os.path.isfile(os.path.join(conf.gate_path_jobs, id)):
        warning("@delete - Job ID not found")
        return "Error: Job with ID:%s not found" % id

    if os.path.exists(os.path.join(conf.gate_path_removed, id)):
        warning("@delete - Job already marked for removal")
        return "Error: Job with ID:%s not found" % id

    try:
        os.symlink(os.path.join(conf.gate_path_jobs, id),
                   os.path.join(conf.gate_path_removed, id))
    except:
        error("@delete - Unable to mark job for removal", exc_info=True)
        return("Error: Unable to mark job %s for removal" % id)

    return "success"
