from oslo_config import cfg

from common.database_adapter import DatabaseAdapter
from common.google_utils import  GoogleClientFetcher

conf = cfg.CONF

database_opts = [
cfg.StrOpt('host', default='localhost', help= 'The host in which the database is currently running.'),
cfg.IntOpt('port', default=3307,  help= 'The port in which the database is running.'),
cfg.StrOpt('username', default=None, help= 'The username with which the database can connect to.'),
cfg.StrOpt('password', default=None, help= 'The password with which the database can connect to'),
cfg.StrOpt('database', default='admin', help= 'The auth database to which the connection is made.')
                 ]

mail_config_opts =[
cfg.StrOpt('app_type', default='web', choices=['web', 'installed'],
           help='Specifies the type of application credentials being used, either "web" for web applications or "installed" for desktop/mobile apps.'),
cfg.StrOpt('project_id', default=None, help='The unique ID of the Google Cloud project associated with the credentials.'),
cfg.StrOpt('client_id', default=None, help='The client ID of the OAuth 2.0 credentials used to authenticate requests to the Google APIs.'),
cfg.StrOpt('client_secret', default=None, help='The client secret associated with the OAuth 2.0 client ID used for authentication.'),
cfg.StrOpt('redirect_uris', default=None, help='A list of authorized redirect URIs for the OAuth 2.0 credentials, which specify where the response should be sent after authorization.'),
cfg.StrOpt('authorization_code', default=None, help='The authorization code obtained after user consent, used to exchange for an access token in OAuth 2.0 flow.'),

                 ]

parser_opts = [
cfg.StrOpt('mail_parse', default='me', help= 'The auth database to which the connection is made.'),

]
# Register your options within the config group
conf.register_opts(database_opts, group='database')
conf.register_opts(mail_config_opts, group='mail_config')
conf.register_opts(parser_opts, group='mail_parser')



def startup_sanity_checks():
    from common import database_adapter
    from common import google_utils
    if not any([cfg.CONF.database.username, cfg.CONF.database.password]):
            raise Exception("You must specify both a username and a password.")

    if not any([cfg.CONF.mail_config.project_id, cfg.CONF.mail_config.client_id, cfg.CONF.mail_config.client_secret,
                cfg.CONF.mail_config.redirect_uris]):
            raise Exception("Project ID, Client Id, Client Secret and Redirect URIs are missing.")

    database_adapter.instance = DatabaseAdapter()
    google_utils.instance = GoogleClientFetcher()
