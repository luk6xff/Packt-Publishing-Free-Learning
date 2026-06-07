import re

from .api import (
    DEFAULT_PAGINATION_SIZE,
    PACKT_API_FREE_LEARNING_CLAIM_URL,
    PACKT_API_PRODUCTS_URL,
    PACKT_PRODUCT_SUMMARY_URL,
)
from .utils.logger import get_logger

logger = get_logger(__name__)

PACKT_FREE_LEARNING_URL = "https://www.packtpub.com/free-learning"


def fetch_all_books_data(api_client, offset=0, data_acc=None):
    """Fetch all pages from user's owned products endpoint."""
    data_acc = data_acc if data_acc is not None else []

    while True:
        response = api_client.get(
            PACKT_API_PRODUCTS_URL,
            params={
                "sort": "createdAt:desc",
                "offset": offset,
                "limit": DEFAULT_PAGINATION_SIZE,
            },
        )
        response_json = response.json()
        books = response_json.get("data") or []
        total = response_json.get("count")
        data_acc.extend(books)

        # If total isn't present, stop when page size drops below requested limit.
        if total is None:
            if len(books) < DEFAULT_PAGINATION_SIZE:
                return data_acc
        elif offset + DEFAULT_PAGINATION_SIZE >= total:
            return data_acc

        offset += DEFAULT_PAGINATION_SIZE


def get_all_books_data(api_client):
    """Fetch all user's ebooks data."""
    logger.info("Getting your books data...")
    try:
        all_books = fetch_all_books_data(api_client)

        ids, my_books_data = (set(), [])
        for book in all_books:
            product_id = book.get("productId") or book.get("id")
            title = book.get("productName") or book.get("title")
            if product_id and title and product_id not in ids:
                ids.add(product_id)
                my_books_data.append({"id": product_id, "title": title})

        logger.info("Books data has been successfully fetched.")
        return my_books_data
    except (AttributeError, TypeError):
        logger.error("Couldn't fetch user's books data.")
        return []


def _extract_offer_data(free_learning_html):
    offer_id_match = re.search(r'offerId="([^"]+)"', free_learning_html)
    offer_id = offer_id_match.group(1) if offer_id_match else None

    product_id_match = re.search(r"const metaProductId = '([^']+)';", free_learning_html)
    if not product_id_match:
        product_id_match = re.search(r'metaProductId\s*=\s*"([^"]+)"', free_learning_html)
    product_id = product_id_match.group(1) if product_id_match else None

    return offer_id, product_id


def claim_product(api_client, recaptcha_solution):
    """Grab Packt Free Learning ebook."""
    logger.info("Start grabbing ebook...")

    free_learning_html = api_client.get(PACKT_FREE_LEARNING_URL).text
    offer_id, product_id = _extract_offer_data(free_learning_html)

    # Handle case when there is no Free Learning offer
    if not offer_id or not product_id:
        logger.info("There is no Free Learning offer right now")
        raise Exception("There is no Free Learning offer right now")

    product_response = api_client.get(PACKT_PRODUCT_SUMMARY_URL.format(product_id=product_id))
    product_json = product_response.json() if product_response.status_code == 200 else {}
    product_title = (
        ((product_json.get("data") or {}).get("title"))
        or product_json.get("title")
        or "Unknown title"
    )
    product_data = {"id": product_id, "title": product_title}

    if any(product_id == book["id"] for book in get_all_books_data(api_client)):
        logger.info('You have already claimed Packt Free Learning "{}" offer.'.format(product_data["title"]))
        return product_data

    claim_response = api_client.post(
        PACKT_API_FREE_LEARNING_CLAIM_URL.format(offer_id=offer_id),
        json={"recaptcha": recaptcha_solution},
    )

    if claim_response.status_code == 200:
        logger.info('A new Packt Free Learning ebook "{}" has been grabbed!'.format(product_data["title"]))
    elif claim_response.status_code == 409:
        logger.info('You have already claimed Packt Free Learning "{}" offer.'.format(product_data["title"]))
    else:
        logger.error("Claiming Packt Free Learning book has failed.")

    return product_data
