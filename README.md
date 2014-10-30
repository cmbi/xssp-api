[![Build Status](https://travis-ci.org/cmbi/xssp-rest.svg?branch=develop)](https://travis-ci.org/cmbi/xssp-rest)

xssp-rest is a REST wrapper around the [xssp][1] `mkhssp` and `mkdssp`
applications. It uses a celery queue to manage requests to prevent overloading
the machine.

# Deploy

A [fabfile][2] is provided to automate the deployment. To start deployment,
download the code to your local machine and run `fab deploy`. You will be
prompted for a deployment mode, which can be either `test` or `prod`.

Some aspects of the deployment script require manual interaction.

## Test

The `test` mode deploys to [VirtualBox][3] virtual machine using [vagrant][4].
You will need to install these packages in order to use this mode, and run
`vagrant up` from the project's root folder.

This mode should be used for testing purposes.

This mode always deploys the `develop` branch.

## Production

The `production` mode deploys to the host given by the user when prompted. This
mode should be used for deploying to the production environment.

This mode always deploys the `master` branch.

[1]: https://github.com/cmbi/xssp
[2]: http://www.fabfile.org/en/latest/
[3]: http://virtualbox.org/
[4]: http://www.vagrantup.com/
