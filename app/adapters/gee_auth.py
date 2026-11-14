"""
Google Earth Engine (GEE) Authentication and Initialization Manager.
Supports:
1. Service Account auth via EE_SERVICE_ACCOUNT and EE_PRIVATE_KEY_FILE.
2. User OAuth / Cloud Project via EE_PROJECT (after running 'earthengine authenticate --project <id>').
3. Auto-loading from .env file if present in workspace.
"""
import os
import sys
import logging
from typing import Tuple, Optional

logger = logging.getLogger("kisanradar.gee")

_EE_INITIALIZED = False
_EE_INIT_ERROR: Optional[str] = None


def load_env_file():
    """Lightweight .env loader without external dependencies."""
    search_dirs = [
        os.getcwd(),
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ]
    for d in search_dirs:
        env_path = os.path.join(d, ".env")
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'\"")
                            if k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass


def init_ee() -> Tuple[bool, Optional[str]]:
    """
    Attempt to initialize Earth Engine using environment variables, .env, or credentials.
    Returns (success: bool, error_message: Optional[str])
    """
    global _EE_INITIALIZED, _EE_INIT_ERROR
    if _EE_INITIALIZED:
        return True, None

    load_env_file()

    try:
        import ee
    except ImportError:
        _EE_INIT_ERROR = "earthengine-api is not installed. Run: pip install earthengine-api"
        return False, _EE_INIT_ERROR

    ee_sa = os.getenv("EE_SERVICE_ACCOUNT")
    ee_key = os.getenv("EE_PRIVATE_KEY_FILE")
    ee_project = os.getenv("EE_PROJECT")

    # 1. Service Account authentication
    if ee_sa and ee_key and os.path.exists(ee_key):
        try:
            credentials = ee.ServiceAccountCredentials(ee_sa, ee_key)
            ee.Initialize(credentials, project=ee_project)
            _EE_INITIALIZED = True
            logger.info("Google Earth Engine initialized via Service Account.")
            return True, None
        except Exception as e:
            _EE_INIT_ERROR = f"GEE Service Account auth failed: {str(e)}"
            return False, _EE_INIT_ERROR

    # 2. User OAuth credentials + Cloud Project
    try:
        if ee_project:
            ee.Initialize(project=ee_project)
        else:
            ee.Initialize()
        _EE_INITIALIZED = True
        logger.info(f"Google Earth Engine initialized successfully (Project: {ee_project or 'default'}).")
        return True, None
    except Exception as e:
        err_str = str(e)
        _EE_INIT_ERROR = (
            f"GEE auth failed: {err_str}\n"
            "Action required:\n"
            "1. Run in your terminal: earthengine authenticate --project <YOUR_GOOGLE_CLOUD_PROJECT_ID>\n"
            "2. Set EE_PROJECT=<YOUR_PROJECT_ID> in .env or environment variable."
        )
        return False, _EE_INIT_ERROR
