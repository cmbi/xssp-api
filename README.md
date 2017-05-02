[![Build Status](https://travis-ci.org/cmbi/xssp-api.svg?branch=develop)](https://travis-ci.org/cmbi/xssp-api)

xssp-api is a REST wrapper around the [xssp][1] `mkhssp` and `mkdssp`
applications. It uses a celery queue to manage requests to prevent overloading
the machine.

# Development

## Installation

Clone the repository and cd into the project folder:

    git clone https://github.com/cmbi/xssp-api.git
    cd xssp-api

Create a python virtual environment:

    mkvirtualenv --no-site-packages xssp-api

Install the dependencies:

    pip install -r requirements
    bower install

Run the unit tests to check that everything works:

    ./test_unit.sh

## Running

Open a terminal window and run:

    ./run.sh

Open another terminal window and run:

    ./run_celery.sh

[1]: https://github.com/cmbi/xssp
