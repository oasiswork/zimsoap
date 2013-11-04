define unsecure_zimbra_user($username = $title, $domain = 'zimbratest.oasiswork.fr'){
  zimbra_user {"${username}":
      ensure       => present,
      domain       => "${domain}",
      aliases      => [],
      user_name    =>  "${username}",
      pwd          => "${username}",
      mailbox_size => '10M';
  }
}

file { '/etc/motd':
  content => "Welcome to zimbra test machine
  Managed by Puppet.\n"
}


# Domains
zimbra_domains {'zimbratest.oasiswork.fr' : ensure => present}
zimbra_domains {'zimbratest2.oasiswork.fr': ensure => present}
zimbra_domains {'zimbratest3.oasiswork.fr': ensure => present}


# Users
unsecure_zimbra_user {'albacore'     : domain => 'zimbratest.oasiswork.fr';}
unsecure_zimbra_user {'barracuda'    : domain => 'zimbratest.oasiswork.fr';}
unsecure_zimbra_user {'carp'         : domain => 'zimbratest.oasiswork.fr';}
unsecure_zimbra_user {'dorado'       : domain => 'zimbratest.oasiswork.fr';}
unsecure_zimbra_user {'emperor'      : domain => 'zimbratest.oasiswork.fr';}

Zimbra_domains['zimbratest.oasiswork.fr'] -> Unsecure_zimbra_user['albacore', 'barracuda', 'carp', 'dorado', 'emperor']

unsecure_zimbra_user {'footballfish' : domain => 'zimbratest2.oasiswork.fr';}
unsecure_zimbra_user {'grenadier'    : domain => 'zimbratest2.oasiswork.fr';}
unsecure_zimbra_user {'haddock'      : domain => 'zimbratest2.oasiswork.fr';}
unsecure_zimbra_user {'inanga'       : domain => 'zimbratest2.oasiswork.fr';}
unsecure_zimbra_user {'javelin'      : domain => 'zimbratest2.oasiswork.fr';}

Zimbra_domains['zimbratest2.oasiswork.fr'] -> Unsecure_zimbra_user['footballfish', 'grenadier', 'haddock', 'inanga', 'javelin']

unsecure_zimbra_user {'kokopu'       : domain => 'zimbratest3.oasiswork.fr';}
unsecure_zimbra_user {'longfin'      : domain => 'zimbratest3.oasiswork.fr';}
unsecure_zimbra_user {'mackerel'     : domain => 'zimbratest3.oasiswork.fr';}
unsecure_zimbra_user {'nase'         : domain => 'zimbratest3.oasiswork.fr';}
unsecure_zimbra_user {'opah'         : domain => 'zimbratest3.oasiswork.fr';}


Zimbra_domains['zimbratest3.oasiswork.fr'] -> Unsecure_zimbra_user['kokopu', 'longfin', 'mackerel', 'nase', 'opah']
