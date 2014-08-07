# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "puppetlabs/ubuntu-14.04-32-puppet"

  config.vm.provision :shell do |shell|
    shell.inline = "apt-get update;"
  end

  config.vm.network :forwarded_port, guest: 8013, host: 8013

  # The sprot.fasta and trembl.fasta files must be in /data/fasta on your local
  # machine. The following line makes this location available to the guest.
  config.vm.synced_folder "/data/fasta", "/data/fasta"
end
