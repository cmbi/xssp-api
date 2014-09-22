from __future__ import print_function

import os

from fabric.api import cd, env, local, prefix, prompt, run, sudo, task
from fabric.contrib.files import exists


# Add -i to sudo calls so the user's environment is loaded (when user parameter
# is specified). In short: it allows command to expand things like '~'.
env.sudo_prefix = "sudo -S -i -p '%(sudo_prompt)s' " % env


def apt(package_list):
    for dep in package_list:
        output = run('apt-cache policy {} | grep Installed'.format(dep))
        if '(none)' in output:
            print("Installing '{}' using apt".format(dep))
            sudo("apt-get -y install {}".format(dep))
        else:
            print("'{}' already installed: {}".format(dep, output[11:]))


def git(url, location, user='root', branch='master'):
    project_name = os.path.split(url)[1].rsplit('.', 1)[0]
    project_path = os.path.join(location, project_name)
    print("Downloading source from '{}' to '{}'".format(url, project_path))

    if exists(project_path):
        with cd(project_path):
            sudo("git pull", user=user)
    else:
        with cd(location):
            sudo("git clone {}".format(url), user=user)

    # Switch to the correct branch depending on the mode
    with cd(project_path):
        sudo("git checkout {}".format(branch), user=user)


def install_xssp():
    # NOTE: The dependencies for XSSP are installed here, but this is the
    #       wrong place. The XSSP project should also provide a fabfile-like
    #       script to automate this, which should then be called from here. A
    #       deb package would be wonderful.
    # TODO: Check if it's installed first.
    # TODO: develop branch required because a new release must be made

    # libzeep is required (until hsspsoap is removed from xssp). Install this
    # first.
    apt(['build-essential', 'autoconf', 'libboost1.54-all-dev', 'libbz2-dev'])

    url = "http://downloads.sourceforge.net/project/libzeep/libzeep-3.0.2.tgz"
    filename = os.path.split(url)[1]
    with cd("~"):
        run("wget {}".format(url))
        run("tar zxvf {}".format(filename))
    # with cd("/home/vagrant/{}".format(filename.rsplit('.', 1)[0])):
        # run("make")
        # sudo("make install")

    # # Build xssp itself now
    git("https://github.com/cmbi/xssp.git", "~", "vagrant")
    # with cd("/home/vagrant/xssp"):
    #     run("autoreconf -i")
    #     run("./configure")
    #     run("make")
    #     sudo("make install")
    prompt("Manually install xssp and press enter when ready")


def prepare():
    # Install dependencies using apt
    apt(['nginx', 'git', 'python-pip', 'python-dev', 'supervisor',
         'rabbitmq-server', 'redis-server'])

    # Install dependencies using pip. These dependencies are installed to the
    # system-wide python environment.
    PIP_DEPENDENCIES = ['virtualenvwrapper']
    for dep in PIP_DEPENDENCIES:
        output = run('pip list | grep {}'.format(dep), quiet=True)
        if output == "":
            print("Installing '{}' using pip".format(dep))
            sudo("pip install {}".format(dep))
        else:
            print("'{}' already installed: {}".format(dep, output.split()[1]))

    # Install xssp
    # TODO: Automate this step.
    # This is commented out because libzeep is a pain to compile, with the
    # result changing depending on the machine. As this will soon be removed
    # from xssp, it's not worth spending time on now. Sadly, this means it must
    # be manually installed.
    install_xssp()

    # Create xssp-rest user
    output = run("cat /etc/passwd | grep xssp-rest", quiet=True)
    if output == "":
        if not exists("/srv/www"):
            print("Creating /srv/www")
            sudo("mkdir /srv/www; chown www-data:www-data /srv/www")
        print("Creating user xssp-rest")
        sudo("useradd -m -d /srv/www/xssp-rest xssp-rest")
        print("Set password for xssp-rest")
        sudo("passwd xssp-rest")
    else:
        print("User xssp-rest already exists")


def upload():
    git("https://github.com/cmbi/xssp-rest.git",
        "/srv/www/xssp-rest",
        "xssp-rest",
        env.branch)


def install():
    # Create the virtual environment if it doesn't already exist.
    with prefix(". /usr/local/bin/virtualenvwrapper.sh"):
        output = sudo('lsvirtualenv -b | grep xssp-rest', user='xssp-rest')
        if output == "":
            print("Creating virtual environment")
            sudo("mkvirtualenv --no-site-packages xssp-rest", user='xssp-rest')
        else:
            print("Virtual environment already exists")

    # Install packages listed in requirements file
    print("Installing virtual environment packages")
    with cd("/srv/www/xssp-rest/xssp-rest"):
        with prefix(". /usr/local/bin/virtualenvwrapper.sh; workon xssp-rest"):
            sudo("pip install -r requirements", user='xssp-rest')

    # Copy the supervisor config, then replace the <PORT> identifier with the
    # correct port number, which the user will give us.
    print("Installing supervisor config file")
    sudo("cp /srv/www/xssp-rest/xssp-rest/supervisor.conf " +
         "/etc/supervisor/conf.d/xssp-rest.conf")
    prompt("Enter xssp-rest port number: ", 'xssp_rest_port', validate=int)
    sudo("sed -i s/\<PORT\>/{}/ {}".format(
        env.xssp_rest_port, '/etc/supervisor/conf.d/xssp-rest.conf'))

    # Copy the nginx config, then replace the <PORT> identifier with the
    # correct port number, which the user will give us.
    print("Installing the nginx config file")
    sudo("cp /srv/www/xssp-rest/xssp-rest/nginx.conf " +
         "/etc/nginx/sites-available/xssp-rest")
    sudo("sed -i s/\<PORT\>/{}/ {}".format(
         env.xssp_rest_port, '/etc/nginx/sites-available/xssp-rest'))
    if not exists("/etc/nginx/sites-enabled/xssp-rest"):
        sudo("ln -s /etc/nginx/sites-available/xssp-rest " +
             "/etc/nginx/sites-enabled/xssp-rest")

    # Copy the xssp-rest config file.
    # This just creates an empty file for now because there are no extra
    # settings.
    sudo("touch /etc/xssp-rest.cfg")


@task
def restart():
    """Restart xssp-rest using supervisorctl"""
    print("Restarting xssp-rest")
    sudo("supervisorctl restart xssp-rest")
    print("Restarting nginx")
    sudo("sudo service nginx restart")


@task
def deploy():
    mode = prompt("Enter the deployment mode ('test' or 'prod'): ")
    print("Deploying xssp-rest to '{}' environment".format(mode))

    if mode == 'test':
        # Parse the vagrant ssh-config information to get the ip address, port,
        # and ssh key_filename so fabric can connect to vagrant.
        output = local('vagrant ssh-config | grep IdentityFile', capture=True)
        env.user = 'vagrant'
        env.host_string = '127.0.0.1:2222'
        env.key_filename = output.split()[1]
        env.branch = 'develop'
    elif mode == 'prod':
        env.branch = 'master'
    else:
        print("Environment '{}' not recognised.")
        exit(1)

    prepare()
    upload()
    install()
    restart()
