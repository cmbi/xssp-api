"""
This example client takes a PDB file, sends it to the REST service, which
creates HSSP data. The HSSP data is then output to the console.

Example:

    python pdb_to_hssp.py 1crn.pdb https://www3.cmbi.umcn.nl/xssp/
"""

import argparse
import json
import requests
import time


def pdb_to_hssp(pdb_file_path, rest_url):
    # Read the pdb file data into a variable
    files = {'file_': open(pdb_file_path, 'rb')}

    # Send a request to the server to create hssp data from the pdb file data.
    # If an error occurs, an exception is raised and the program exits. If the
    # request is successful, the id of the job running on the server is
    # returned.
    url_create = '{}api/create/pdb_file/hssp_hssp/'.format(rest_url)
    r = requests.post(url_create, files=files)
    r.raise_for_status()

    job_id = json.loads(r.text)['id']
    print "Job submitted successfully. Id is: '{}'".format(job_id)

    # Loop until the job running on the server has finished,
    # either successfully or due to an error.
    ready = False
    n_polls = 0
    max_polls = 240
    while not ready:
        # Check the status of the running job. If an error occurs an exception
        # is raised and the program exits. If the request is successful, the
        # status is returned.
        url_status = '{}api/status/pdb_file/hssp_hssp/{}/'.format(rest_url,
                                                                  job_id)
        r = requests.get(url_status)
        r.raise_for_status()

        status = json.loads(r.text)['status']
        print "Job status is: '{}'".format(status)

        # If the status equals SUCCESS, exit out of the loop by changing the
        # condition ready. This causes the code to drop into the `else` block
        # below.
        #
        # If the status equals either FAILURE or REVOKED, an exception is
        # raised containing the error message. The program exits.
        #
        # Otherwise, wait for thirty seconds and start at the beginning of the
        # loop again.
        if status == 'SUCCESS':
            ready = True
        elif status in ['FAILURE', 'REVOKED']:
            raise Exception(json.loads(r.text)['message'])
        else:
            n_polls = n_polls + 1

        # Stop waiting when there appears to be a server-side problem
        if n_polls > max_polls:
            raise Exception('The server is taking too long to finish the job.')

        time.sleep(30)
    else:
        # Requests the result of the job. If an error occurs an exception is
        # raised and the program exits. If the request is successful,
        # the result is returned.
        url_result = '{}api/result/pdb_file/hssp_hssp/{}/'.format(rest_url,
                                                                  job_id)
        r = requests.get(url_result)
        r.raise_for_status()
        result = json.loads(r.text)['result']

        # Return the result to the caller, which prints it to the screen.
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create HSSP from a PDB file')
    parser.add_argument('pdb_file_path')
    parser.add_argument('rest_url')
    args = parser.parse_args()

    result = pdb_to_hssp(args.pdb_file_path, args.rest_url)
    print result
