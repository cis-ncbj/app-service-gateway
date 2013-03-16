import os
import shutil
import tempfile
import uuid
import logging
import stat
import simplejson as json

from logging import debug

#logging.basicConfig(filename='/tmp/webservice.log',level=logging.DEBUG)

#TODO read from ini/json file
allowed_services = ['Test', 'MultiNest'] # List of allowed service names
comm_path = '/opt/klimasz/www/webservice' # Directory where files with job descriptions are stored
output_url = 'http://buldog.fuw.edu.pl/upload/webservice' # Base URL for output files

jobs_dir = os.path.join(comm_path, 'jobs') # Subdir where active job identifiers are stored
queue_dir = os.path.join(comm_path, 'queue') # Subdir for queued jobs
running_dir = os.path.join(comm_path, 'running') # Subdir for running jobs
done_dir = os.path.join(comm_path, 'done') # Subdir for finished jobs
delete_dir = os.path.join(comm_path, 'delete') # Subdir for jobs to be removed

def submit(request):
    """Submit a job request to the processing queue.

    Arguments:
    request - dictionary with requests' attributes. A "service" attribute with valid value is required.
              Other atributes will be passed to the PBS script by job manager service after verification.

    Output: Job ID

    Creates a file with job description in JSON format. File name is unique and serves as job ID.
    The job is added to the queue for execution.
    """
    # Request is required to define service keyword
    if 'service' not in request.keys():
        return 'Error: Missing service name'
    debug('Service defined: %s'%request['service'])

    # Only request for aupported services are processed
    if request['service'] not in allowed_services:
        return 'Error: Unsupported service'
    debug("Service selected: %s"%request['service'])

    try:
        # Create file to store the input data
        # The file name is unique and will be used as request ID
        # Add UUID into the mix to allow for more then ~250k concurent ids
        prefix = request['service'] + '_' + str(uuid.uuid4()) + '_'
        (fd, name) = tempfile.mkstemp(prefix=prefix, dir=jobs_dir)
        f = os.fdopen(fd, 'w')
        debug("File created")
        # Dump input data in JSON format (handle utf8 characters)
        f.write(json.dumps(request, ensure_ascii=False).encode('utf-8'))
        f.close()
        # Workaround until webserver an jobmanager run as same user
        _st = os.stat(name)
        os.chmod(name, _st.st_mode | stat.S_IRGRP | stat.S_IWGRP |
                stat.S_IROTH |stat.S_IWOTH )
        debug("Data written")
        # Mark request as queued
        os.symlink(name, os.path.join(queue_dir, os.path.basename(name)))
    #except Exception as e: #for python >= 2.6
    except Exception, e:
        return "Error: Exception cought while creating job request: %s"%e

    debug("Return request id: %s"%os.path.basename(name))
    return os.path.basename(name)

def status(id):
    """Check the status of a job identified by id.

    Output: Job status [queued, running, done]

    Returns Errors if id does not exist or job is not in done state.
    """
    # Check if the job exists (file with it's id should be present in jobs subdir)
    if not os.path.isfile(os.path.join(jobs_dir, id)):
        return "Error: Job with ID:%s not found"%id
    debug("Job found")

    if os.path.exists(os.path.join(delete_dir, id)):
        debug("Job deleted")
        return "Error: Job with ID:%s not found"%id

    # Check for symlinks in queue, running and done subdirs
    if os.path.exists(os.path.join(queue_dir, id)):
        debug("Job queued")
        return "queued"
    elif os.path.exists(os.path.join(running_dir, id)):
        debug("Job running")
        return "running"
    elif os.path.exists(os.path.join(done_dir, id)):
        debug("Job done")
        return "done"
    else:
        debug("Job deleted")
        return "Error: Job with ID:%s not found"%id

def output(id):
    """Return base URL for output files for job identified by id.

    Output: URL

    Returns Errors if id does not exist or job is not in done state.
    """
    # Check if the job exists (file with it's id should be present in jobs subdir)
    if not os.path.isfile(os.path.join(jobs_dir, id)):
        return "Error: Job with ID:%s not found"%id
    debug("Job found")

    if os.path.exists(os.path.join(delete_dir, id)):
        debug("Job deleted")
        return "Error: Job with ID:%s not found"%id

    # Check for symlinks in queue, running and done subdirs
    if not os.path.exists(os.path.join(done_dir, id)):
        return "Error: Job with ID:%s is not in done state."%id

    return output_url + '/' + id

def delete(id):
    """Mark job idendified with id for deletion.
    
    The actual job removal along with related files is perfromed by job manager service.
    """

    # Check if the job exists (file with it's id should be present in jobs subdir)
    if not os.path.isfile(os.path.join(jobs_dir, id)):
        return "Error: Job with ID:%s not found"%id
    debug("Job found")

    if os.path.exists(os.path.join(delete_dir, id)):
        debug("Job deleted")
        return "Error: Job with ID:%s not found"%id

    os.symlink(os.path.join(jobs_dir, id), os.path.join(delete_dir, id))

    return "success"

