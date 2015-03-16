# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.define "8.0.4p" do |that|
		that.vm.box = "zimbra-8.0.4p"
		that.vm.box_url = "http://vagrant.owk.cc/zimbra-8.0.4p.box"
  end

  config.vm.define "8.0.5" do |that|
		that.vm.box = "zimbra-8.0.5"
		that.vm.box_url = "http://vagrant.owk.cc/zimbra-8.0.5.box"
  end

  # hostname
  config.vm.hostname = "zimbratest.oasiswork.fr"

  config.vm.network :private_network, ip: "192.168.33.10"

  config.vm.provision "puppet" do |puppet|
    puppet.module_path = "modules"
  end

	# Adds a preauth key for the first domain if non-existant
  config.vm.provision "shell",
	inline: "sudo su - zimbra -c  'zmprov gdpak zimbratest.oasiswork.fr  > /dev/null 2>&1 ;/bin/true'"

end
