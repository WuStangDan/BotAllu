import requests
import json
from replit import db


def pull_deals():
    response = requests.get(
        "https://cheapshark.com/api/1.0/deals?storeID=1&pageSize=50"
    )
    if response.status_code != 200:
        return None

    json_data = json.loads(response.text)
    for deal in json_data:
        if deal["steamRatingText"] != "Overwhelmingly Positive":
            continue
        if float(deal["savings"]) < 90.0:
            continue

        # Skip if already posted deal.
        if deal["dealID"] in db["dealIDs"]:
            continue

        db["dealIDs"][deal["dealID"]] = "posted"
        deal_text = deal["title"] + " - $" + deal["salePrice"]
        deal_text += "\n\n"
        deal_text += "https://www.cheapshark.com/redirect?dealID=" + deal["dealID"]
        return deal_text

    # No deal found.
    return None
