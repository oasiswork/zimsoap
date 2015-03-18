import ConfigParser
from os.path import join, dirname

defaults = {
    'host'           : '192.168.33.10',
    'admin_port'     : '7071',
    'domain_1'       : 'zimbratest.oasiswork.fr',
    'domain_2'       : 'zimbratest2.oasiswork.fr',
    'domain_3'       : 'zimbratest3.oasiswork.fr',
    'admin_login'    : 'admin@zimbratest.oasiswork.fr',
    'admin_password' : 'password',
    'lambda_user'    : 'albacore@zimbratest.oasiswork.fr',
    'lambda_password': 'albacorealbacore',
    'calres1'        : 'camescope@zimbratest2.oasiswork.fr'}

def get_config():
    parser = ConfigParser.SafeConfigParser(defaults=defaults)
    parser.read(join(dirname(__file__),'test_config.ini'))
    try:
        return {k:v for k,v in parser.items('zimbra_server')}
    except ConfigParser.NoSectionError:
        # In case there is no file at all
        return defaults
