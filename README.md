xssp-rest is a REST wrapper around the [xssp][1] `mkhssp` and `mkdssp`
applications. It uses a celery queue to manage requests to prevent overloading
the machine.

# REST API

The methods available in the API are documented below. Note that all parameters
and response are in JSON.

## `/create/dssp/from_pdb/` (POST)

Submits a job to produce DSSP content from PDB content. On success a job id is
returned which can be used in subsequent API calls.

* Arguments
** `pdb_content`: The content of the PDB file as a string

* Responses
** Success (202)
*** `id`: The id of the job
** Failure (400)

## `/create/hssp/from_pdb/` (POST)

Submits a job to produce HSSP content from PDB content. On success a job id is
returned which can be used in subsequent API calls.

* Arguments
** `pdb_content`: The content of the PDB file as a string

* Responses
** Success (202)
*** `id`: The id of the job
** Failure (400)

## `/create/hssp/from_sequence/` (POST)

Submits a job to produce HSSP content from a protein sequence. On success a job
id is returned which can be used in subsequent API calls.

* Arguments
** `sequence`: The content of the PDB file as a string

* Responses
** Success (202)
*** `id`: The id of the job
** Failure (400)

## `/job/<job_type>/<job_id>/status/` (GET)

Gets the status of a previous job submission.

* Arguments
** `job_type`: Either `dssp_from_pdb`, `hssp_from_pdb`, or `hssp_from_sequence`
** `job_id`: The id of the job to get the status for, returned by a previous
             API call.

* Responses
** Success (200)
*** `status`: One of the [celery tasks status values][2].
** Failure (400)

## `/job/<job_type>/<job_id>/result/` (GET)

Gets the results of a previous job submission.

* Arguments
** `job_type`: Either `dssp_from_pdb`, `hssp_from_pdb`, or `hssp_from_sequence`
** `job_id`: The id of the job to get the status for, returned by a previous
             API call.

* Responses
** Success (200)
*** `result`: The result of the job submission.
** Failure (400)

[1]: https://github.com/cmbi/xssp
[2]: http://celery.readthedocs.org/en/latest/userguide/tasks.html#built-in-states
