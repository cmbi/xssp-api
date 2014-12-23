[![Build Status](https://travis-ci.org/cmbi/xssp-rest.svg?branch=develop)](https://travis-ci.org/cmbi/xssp-rest)

xssp-rest is a REST wrapper around the [xssp][1] `mkhssp` and `mkdssp`
applications. It uses a celery queue to manage requests to prevent overloading
the machine.

[1]: https://github.com/cmbi/xssp
