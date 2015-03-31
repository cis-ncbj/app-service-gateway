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
        debug('Error: Missing service name')
        return 'Error: Missing service name'
    debug('Service defined: %s' % request['service'])

    # Only request for supported services are processed
    if request['service'] not in conf.allowed_services:
        debug('Error: Missing service name')
        return 'Error: Unsupported service'
    debug("Service selected: %s" % request['service'])

    try:
        # Create file to store the input data
        # The file name is unique and will be used as request ID
        # Add UUID into the mix to allow for more then ~250k concurent ids
        _prefix = request['service'] + '_' + str(uuid.uuid4()) + '_'
        (_fd, _name) = tempfile.mkstemp(prefix=_prefix, dir=conf.gate_path_jobs)
        _jid = os.path.basename(_name)
        _f = os.fdopen(_fd, 'w')
        debug("Job ID file created")
        # Dump input data in JSON format (handle utf8 characters)
        _f.write(json.dumps(request, ensure_ascii=False).encode('utf-8'))
        _f.close()
        # Workaround until webserver an jobmanager run as same user
        _st = os.stat(_name)
        os.chmod(_name, _st.st_mode | stat.S_IRGRP | stat.S_IWGRP |
                 stat.S_IROTH | stat.S_IWOTH)
        debug("Job request data written to Job ID file")
        # Mark request as queued
        os.symlink(
            _name,
            os.path.join(conf.gate_path_new, _jid)
        )
        # Mark deprecated API calls
        if float(request["api"]) < conf.service_api:
            debug("Job request uses deprecated API")
            _path = os.path.join(conf.gate_path_flag_old_api, _jid)
            os.symlink( _name, _path )

    except Exception as e:
        error("Error: Exception cought while creating job request: %s" % e)
        return "Error: Exception cought while creating job request: %s" % e

    debug("Return request id: %s" % _jid)
    return _jid


def status(id):
    """
    Check the status of a job.

    :param id: Job id to check
    :return: Job status [New, Waiting, Processing, Queued, Running, Closing,
        Cleanup, Done, Failed, Killed, Aborted]. For Done, Failed, Killed and
        Aborted states additional info is provided after ":".
        Returns Error string if id does not exist.
    """
    # Check if the job exists (file with it's id should be present in jobs
    # subdir)
    debug("@status - Status check for job: %s" % id)
    if not os.path.isfile(os.path.join(conf.gate_path_jobs, id)):
        warning("@status - Job ID not found")
        return "Error: Job with ID:%s not found" % id

    try:
        # Check if the job requested deprecated API
        _old_api = False
        if os.path.exists(os.path.join(conf.gate_path_flag_old_api, id)):
            _old_api = True
        # Hide jobs scheduled for removal
        if os.path.exists(os.path.join(conf.gate_path_flag_delete, id)):
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
        elif os.path.exists(os.path.join(conf.gate_path_closing, id)):
            if _old_api:
                _state = 'running'
            else:
                _state = 'closing'
        elif os.path.exists(os.path.join(conf.gate_path_cleanup, id)):
            if _old_api:
                _state = 'running'
            else:
                _state = 'cleanup'
        elif os.path.exists(os.path.join(conf.gate_path_running, id)):
            _state = 'running'
        elif os.path.exists(os.path.join(conf.gate_path_queued, id)):
            _state = 'queued'
        elif os.path.exists(os.path.join(conf.gate_path_processing, id)):
            if _old_api:
                _state = 'waiting'
            else:
                _state = 'processing'
        elif os.path.exists(os.path.join(conf.gate_path_waiting, id)):
            _state = 'waiting'
        elif os.path.exists(os.path.join(conf.gate_path_new, id)):
            if _old_api:
                _state = 'waiting'
            else:
                _state = 'new'
        else:
            error("@status - Job status missing")
            return "Error: Job with ID:%s not found" % id
    except:
        error("@status - Unable to check job status", exc_info=True)
        return "Error: Unable to check job status"

    if _state in ('aborted', 'failed', 'done', 'killed'):
        try:
            with open(os.path.join(conf.gate_path_opts, "message_" + id)) as _status_file:
                return "".join(_status_file.readlines()).strip()
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

    if os.path.exists(os.path.join(conf.gate_path_flag_delete, id)):
        debug("@output - Job marked for removal")
        return "Error: Job with ID:%s not found" % id

    if not os.path.exists(os.path.join(conf.gate_path_done, id)) and \
       not os.path.exists(os.path.join(conf.gate_path_aborted, id)) and \
       not os.path.exists(os.path.join(conf.gate_path_failed, id)):
        return "Error: Job with ID:%s did not finish." % id

    return conf.gate_url_output + "/" + id


def progress(id):
    """
    Return contents of progress.log file if it was generated by the job. Allows
    to update user on progress of calculations.

    :return: Contents of progress.log file. Returns Error string if id does not
        exist.
    """
    # Check if the job exists (file with it's id should be present in jobs
    # subdir)
    debug('@output - Progress log request')
    if not os.path.isfile(os.path.join(conf.gate_path_jobs, id)):
        warning("@output - Job ID not found")
        return "Error: Job with ID:%s not found" % id

    if os.path.exists(os.path.join(conf.gate_path_flag_delete, id)):
        debug("@output - Job marked for removal")
        return "Error: Job with ID:%s not found" % id

    # Return contents of progress.log file if it exists
    _out_dir = os.path.join(conf.gate_path_output, id)
    _progress_log = os.path.join(_out_dir, 'progress.log')
    _output_log = os.path.join(_out_dir, 'output.log')
    if os.path.exists(_progress_log):
        with open(_progress_log) as _log:
            return ''.join(_log.readlines())
    # If no progress.log was found return contents of output.log
    elif (os.path.exists(os.path.join(conf.gate_path_done, id)) or
          os.path.exists(os.path.join(conf.gate_path_failed, id))) and \
            os.path.exists(_output_log):
        with open(_output_log) as _log:
            return ''.join(_log.readlines())

    # All other cases
    return "Waiting ..."


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

    if os.path.exists(os.path.join(conf.gate_path_flag_delete, id)):
        warning("@delete - Job already marked for removal")
        return "Error: Job with ID:%s not found" % id

    try:
        os.symlink(os.path.join(conf.gate_path_jobs, id),
                   os.path.join(conf.gate_path_flag_delete, id))
    except:
        error("@delete - Unable to mark job for removal", exc_info=True)
        return("Error: Unable to mark job %s for removal" % id)

    return "Success"


def kill(id):
    """
    Request job idendified with id to be killed.

    :param id: ID of job to be killed
    """

    # Check if the job exists (file with it's id should be present in jobs
    # subdir)
    debug("@kill - Job remove request %s" % id)
    if not os.path.isfile(os.path.join(conf.gate_path_jobs, id)):
        warning("@kill - Job ID not found")
        return "Error: Job with ID:%s not found" % id

    if os.path.exists(os.path.join(conf.gate_path_flag_stop, id)):
        warning("@kill - Job already marked for a kill")
        return "Error: Job with ID:%s not found" % id

    if os.path.exists(os.path.join(conf.gate_path_new, id)) or \
       os.path.exists(os.path.join(conf.gate_path_waiting, id)) or \
       os.path.exists(os.path.join(conf.gate_path_queued, id)) or \
       os.path.exists(os.path.join(conf.gate_path_running, id)):
        try:
            os.symlink(os.path.join(conf.gate_path_jobs, id),
                       os.path.join(conf.gate_path_flag_stop, id))
        except:
            error("@kill - Unable to mark job for a kill", exc_info=True)
            return("Error: Unable to mark job %s for a kill" % id)
    else:
        warning("@kill - Job already finished")
        return "Error: No active job with ID:%s found" % id

    return "Success"
