# -*- coding: utf-8 -*-
from flask import request

from CISAppGateway import app, Server


@app.route('/')
def index():
    help = """CIŚ webservice REST api.</br>
</br>
This is a proof of concept implementation.</br>
</br>
* Access</br>
[host] = http://buldog.fuw.edu.pl/webservice</br>
</br>
* Supported services</br>
</br>
    ** Test</br>
    *** Attributes:</br>
    *** A : int(0,10000)</br>
    *** B : float(-100,100)</br>
    *** C : ["alpha", "beta", "gamma", "delta"]</br>
</br>
    ** MultiNest</br>
    *** Attributes:</br>
    *** PBS_NODES : int(1,4)</br>
    *** PBS_PPN : int(1,64)</br>
    *** argument : float(-10,10)</br>
    *** live_points : int(0,10000)</br>
    *** function : ["sin", "cos", "log"]</br>
</br>
* Job submission</br>
Jobs are subbited via POST request on [host]/submit</br>
The POST request should contain job attributes either in JSON format or as
FORM </br>
data:</br>
</br>
    curl -X POST -d "service=Test&attr1=value1&attr2=value2" [host]/submit</br>
    curl -X POST -H "Content-type: application/json" [host]/submit \</br>
    -d '{"service":"MultiNest", "live_points":"1000", "nodes":"3"}'</br>
</br>
The request will return an job ID e.g.:
 MultiNest_40ecad7d-41be-48bc-9d87-131f894052a8_nlfsvY</br>
</br>
* Verifying job status</br>
Job status can be queried by GET on [host]/status/[id].
Where [id] is the string</br>
returned during submission.</br>
</br>
    curl
 [host]/status/MultiNest_40ecad7d-41be-48bc-9d87-131f894052a8_nlfsvY</br>
</br>
The request returns: "queued", "running", "done" or an error.</br>
</br>
* Job output</br>
The http/ftp base URL for the output files is retrieved as
 [host]/output/[id]</br>
</br>
    curl
 [host]/output/MultiNest_40ecad7d-41be-48bc-9d87-131f894052a8_nlfsvY</br>
</br>
* Job can be scheduled for removal: [host]/delete/[id]</br>
</br>
    curl
 [host]/delete/MultiNest_40ecad7d-41be-48bc-9d87-131f894052a8_nlfsvY</br>
</br>
* Possible improvements:</br>
    Authentication using OpenID. This would allow to query users jobs.
    With</br>
    addition of "Name" job atribute this would allow to generate a user
    readable</br>
    job list.</br>
"""
    return help


@app.route('/submit', methods=['POST'])
def submit():
    if request.headers['Content-Type'] == 'application/json':
        return Server.submit(request.json)
    else:
        return Server.submit(request.form)


@app.route('/status/<id>')
def status(id):
    return Server.status(id)


@app.route('/output/<id>')
def output(id):
    return Server.output(id)


@app.route('/delete/<id>')
def delete(id):
    return Server.delete(id)
