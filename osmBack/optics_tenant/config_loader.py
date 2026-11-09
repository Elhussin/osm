# config_loader.py
import os
from decouple import Config, RepositoryEnv
# from .settings import DEBUG
# DEBUG = os.getenv("DEBUG", False)
DEBUG = True
if DEBUG:
    ENV_FILE = os.getenv("ENV_FILE", ".env.development") 
else:
    ENV_FILE = os.getenv("ENV_FILE", ".env.production") 

config = Config(RepositoryEnv(ENV_FILE))
