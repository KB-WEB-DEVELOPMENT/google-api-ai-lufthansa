# app/config.py
# -*- coding: utf-8 -*-
import os

class Config(object):
    DEBUG = False
    SQLALCHEMY_ECHO = False
	# to be adjusted
    SECRET_KEY = 'TO_BE_DETERMINED'
    CSRF_ENABLED = True
    # to be adjusted
	CSRF_SESSION_LKEY = 'TO_BE_DETERMINED'

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    SQLALCHEMY_ECHO = True
    LUFTHANSA_OAUTH_CONSUMER_KEY = '7r8cyauaumeg9u3f47kg4xpq'
    LUFTHANSA_OAUTH_CONSUMER_SECRET = 'R7Rm79x5Zf'

class TestingConfig(DevelopmentConfig):
    TESTING = True

class ProductionConfig(Config):
    PRODUCTION = True

# this line may have to be adapted to the server name	
mode = os.environ.get('development_OR_testing_OR_production', 'development')
object = DevelopmentConfig
if mode == 'development':
    object = DevelopmentConfig
elif mode == 'testing':
    object = TestingConfig
elif mode == 'production':
    object = ProductionConfig
else:
    raise ValueError("Unknown config mode.")


