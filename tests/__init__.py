import ConfigParser
from os.path import join, dirname

defaults = {
    'host'           : '192.168.33.10',
    'server_name'    : 'zimbratest.example.com',
    'admin_port'     : '7071',
    'domain_1'       : 'zimbratest.example.com',
    'domain_2'       : 'zimbratest2.example.com',
    'domain_3'       : 'zimbratest3.example.com',
    'admin_login'    : 'admin@zimbratest.example.com',
    'admin_password' : 'password',
    'lambda_user'    : 'albacore@zimbratest.example.com',
    'lambda_password': 'albacorealbacore',
    'calres1'        : 'camescope@zimbratest2.example.com'}

def get_config():
    parser = ConfigParser.SafeConfigParser(defaults=defaults)
    parser.read(join(dirname(__file__),'test_config.ini'))
    try:
        return {k:v for k,v in parser.items('zimbra_server')}
    except ConfigParser.NoSectionError:
        # In case there is no file at all
        return defaults
