"""Module with Packt API client handling API authentication."""
import logging

from curl_cffi import requests

from .utils.logger import get_logger

logger = get_logger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)  # downgrading logging level for requests

PACKT_API_LOGIN_URL = "https://www.packtpub.com/api/login"
PACKT_API_PRODUCTS_URL = "https://www.packtpub.com/api/entitlements/users/me/owned"
PACKT_PRODUCT_SUMMARY_URL = "https://subscription.packtpub.com/api/products/{product_id}/summary"
PACKT_API_PRODUCT_FILE_TYPES_URL = "https://services.packtpub.com/products-v1/products/{product_id}/types"
PACKT_API_PRODUCT_FILE_DOWNLOAD_URL = "https://subscription.packtpub.com/download/{product_id}/{file_type}"
PACKT_API_FREE_LEARNING_CLAIM_URL = "https://www.packtpub.com/api/claim-free-learning/offers/{offer_id}"
DEFAULT_PAGINATION_SIZE = 100


class PacktAPIClient:
    """Packt API client making API requests on script's behalf."""

    def __init__(self, credentials):
        # Packt currently blocks plain requests-based clients frequently; browser impersonation is required.
        self.session = requests.Session(impersonate="chrome")
        self.credentials = credentials
        self.login()

    def login(self):
        """Log user into Packt and initialize authenticated session cookies."""
        try:
            response = self.session.post(PACKT_API_LOGIN_URL, json=self.credentials)
            if response.status_code != 200:
                raise RuntimeError("login failed with status {}".format(response.status_code))
            logger.info("Logged in to Packt successfully!")
        except Exception as e:
            logger.error("Logging in to Packt account failed! {}".format(e))
            raise

    def request(self, method, url, **kwargs):
        """Make a request to a Packt API."""
        kwargs.setdefault("timeout", 60)
        response = self.session.request(method, url, **kwargs)
        if response.status_code == 401:
            # Login again to refresh session cookies and retry request
            self.login()
            return self.session.request(method, url, **kwargs)
        return response

    def get(self, url, **kwargs):
        """Make a GET request to a Packt API."""
        return self.request("get", url, **kwargs)

    def post(self, url, **kwargs):
        """Make a POST request to a Packt API."""
        return self.request("post", url, **kwargs)

    def put(self, url, **kwargs):
        """Make a PUT request to a Packt API."""
        return self.request("put", url, **kwargs)

    def patch(self, url, **kwargs):
        """Make a PATCH request to a Packt API."""
        return self.request("patch", url, **kwargs)

    def delete(self, url, **kwargs):
        """Make a DELETE request to a Packt API."""
        return self.request("delete", url, **kwargs)
