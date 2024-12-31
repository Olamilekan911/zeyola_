class BaseConfig(object):
    ADMIN_EMAIL="test@email.com"

class LiveConfig(BaseConfig):
    SITE_ADDRESS="https://site.com"

class Testconfig(BaseConfig):
    SITE_ADRESS="https://testsite.com"
