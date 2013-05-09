# -*- coding: utf-8 -*-
"""
Flask based implementation of AppGateway REST API. Functions in this module
implement server response to API requests - each request is defined as specific
URL.
"""

from flask import request

from CISAppGateway import app, Server


@app.route('/')
def index():
    """Main page."""
    msg = """Welcome to CIŚ AppGateway"""
    return msg


@app.route('/submit', methods=['POST'])
def submit():
    """
    Submit request. Expects a POST request (@ /submit URL) with data in
    standard FORM format or as JSON payload identified by header:
    'Content-Type' = 'application/json'. Returns JOB ID upon success, error
    otherwise.
    """
    if request.headers['Content-Type'] == 'application/json':
        return Server.submit(request.json)
    else:
        return Server.submit(request.form)


@app.route('/status/<id>')
def status(id):
    """
    Job status request. Expects GET request on /status/<id> URL, where <id> is
    the Job ID returned during submission. Returns job status if job exists,
    error otherwise:

    * waiting
    * queued
    * running
    * done
    * failed
    * aborted
    * killed
    """
    return Server.status(id)


@app.route('/output/<id>')
def output(id):
    """
    Job output request. Expects GET request on /output/<id> URL, where <id> is
    the Job ID returned during submission. Returns base URL for job output
    files. Client is expected to know the actual file names or browse contents
    of the output directory at http server. If job does not exist returns an
    error.
    """
    return Server.output(id)


@app.route('/progress/<id>')
def progress(id):
    """
    Job progress request. Expects GET request on /progress/<id> URL, where <id>
    is the Job ID returned during submission. Returns contents of
    "progress.log" file if it was created by the job. This file should contain
    job log or info about its progress. For jobs that do not generate
    "progress.log" the "output.log" is returned when job enters 'done' or
    'failed' state. If job does not exist returns an error.
    """
    return Server.progress(id)


@app.route('/delete/<id>')
def delete(id):
    """
    Job delete request. Expects GET request on /delete/<id> URL, where <id> is
    the Job ID returned during submission. If job is queued or running it will
    be killed. All files related to the job will be removed. If job does not
    exist returns an error.
    """
    return Server.delete(id)
