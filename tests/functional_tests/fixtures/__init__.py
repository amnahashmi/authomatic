# encoding: utf-8

from os import path
from collections import namedtuple
import pkgutil
import sys
import time
import six
from six.moves import reload_module
from jinja2 import Environment, FileSystemLoader

# Add path of the functional_tests_path package to PYTHONPATH.
# Tis is necessary for the following imports to work when this module is
# imported from the expected_values.* modules.

FUNCTIONAL_TESTS_PATH = path.join(path.dirname(__file__), '..')
sys.path.append(FUNCTIONAL_TESTS_PATH)

from tests.functional_tests import config
from tests.functional_tests import expected_values


# Create template environment to load templates.
TEMPLATES_DIR = path.join(path.abspath(path.dirname(__file__)), '../templates')
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def render_home():
    """Renders the homepage"""

    template = env.get_template('index.html')
    return template.render(providers=ASSEMBLED_CONFIG.keys())


def render_login_result(result):
    """
    Renders the login handler

    :param result:

        The :class:`.authomatic.core.LoginResult` returned by the
        :meth:`.authomatic.Authomatic.login` method.

    """

    reload_module(sys)
    if six.PY2:
        sys.setdefaultencoding('utf-8')

    response = None
    original_credentials = {}
    refreshed_credentials = {}
    if result:
        response_message = ''
        if result.user:
            result.user.update()
            if result.user.credentials:
                original_credentials.update(result.user.credentials.__dict__)
                time.sleep(2)
                response = result.user.credentials.refresh(force=True)
                refreshed_credentials.update(result.user.credentials.__dict__)

        user_properties = list(ASSEMBLED_CONFIG.values())[0]['user'].keys()
        template = env.get_template('login.html')
        return template.render(result=result,
                               providers=ASSEMBLED_CONFIG.keys(),
                               user_properties=user_properties,
                               error=result.error,
                               credentials_response=response,
                               original_credentials=original_credentials,
                               refreshed_credentials=refreshed_credentials)


def get_configuration(provider):
    """
    Creates the user configuration which holds the tested values

    It merges the ``config.COMMON`` and the ``config.PROVIDERS[provider]``
    dictionaries and returns a named tuple.

    :param str:
        Provider slug used in ``config.PROVIDERS``.

    :returns:

        A named tuple.

    """

    # Merge and override common settings with provider settings.
    conf = {}
    conf.update(config.COMMON)
    conf.update(config.PROVIDERS[provider])

    class_name = '{0}Configuration'.format(provider.capitalize())
    Res = namedtuple(class_name, sorted(conf.keys()))

    # Add additional class attributes which are not allowed to be passed
    # to the namedtuple
    Res.email_escaped = conf['user_email'].replace('@', '\u0040')
    Res.no_birth_date = [conf['user_birth_year'], 'birth']
    Res.no_city = [conf['user_city'], 'city']
    Res.no_email = [conf['user_email'], Res.email_escaped, 'email', 'e-mail']
    Res.no_first_name = ['"{0}"'.format(conf['user_first_name']), 'first']
    Res.no_last_name = ['"{0}"'.format(conf['user_last_name']), 'last']
    Res.no_gender = [conf['user_gender'], 'gender']
    Res.no_locale = [conf['user_locale'], 'language', 'locale']
    Res.no_nickname = ['nickname', conf['user_nickname']]
    Res.no_phone = [conf['user_phone'], 'phone']
    Res.no_postal_code = [conf['user_postal_code'], 'postal', 'zip']
    Res.no_timezone = ['timezone']
    Res.no_username = ['username', '"{}"'.format(conf['user_username'])]
    Res.no_location = [conf['user_country'], 'city',
        'country', 'location'] + Res.no_postal_code + Res.no_city

    # Populate the namedtuple with provider settings.
    return Res(**conf)


ASSEMBLED_CONFIG = {}
expected_values_path = path.dirname(expected_values.__file__)

# Loop through all modules of the expected_values package.
for importer, name, ispkg in pkgutil.iter_modules([expected_values_path]):
    # Import the module
    mod = importer.find_module(name).load_module(name)

    # Assemble result
    result = {}
    result.update(config.PROVIDERS[name])
    result.update(mod.CONFIG)
    ASSEMBLED_CONFIG[name] = result