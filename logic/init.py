import os
import json
from dotenv import load_dotenv # type: ignore


def load_mappings():
    load_dotenv()
    THERAPIST_NAME_MAP = json.loads(os.getenv("THERAPIST_NAME_MAP_ENV", "{}")) # load secrets from .env and parse into json
    CPT_CATEGORY_MAP = json.loads(os.getenv("CPT_CATEGORY_MAP_ENV", "{}"))
    return THERAPIST_NAME_MAP, CPT_CATEGORY_MAP

