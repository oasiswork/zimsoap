node default {
  file { '/etc/motd':
    content => "Welcome to your Vagrant-built virtual machine!
    Managed by Puppet.\n"
  }
}
