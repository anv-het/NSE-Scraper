import requests
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup


def get_api_url():
    now = datetime.now()
    month, year = now.month, now.year
    fin_year = f"{year}-{str(year+1)[-2:]}"
    return f"https://webnodejs.investorgain.com/cloud/report/data-read/331/1/{month}/{year}/{fin_year}/0/all"


def extract_text(html_str):
    return BeautifulSoup(html_str or "", "html.parser").get_text(strip=True)


def extract_status(name_html):
    soup = BeautifulSoup(name_html, "html.parser")
    badge = soup.find("span", class_="badge")

    # Map status codes to human-readable format (including Listed)
    status_map = {
        "U": "Upcoming",
        "O": "Open",
        "C": "Closed",
        "CT": "Close Today",
        "L": "Listed",
    }

    if badge:
        status_code = badge.text.strip()
        return status_code, status_map.get(status_code, status_code)

    # If there is no badge, detect Listed from the inline text like "L@65.90 (-0.15%)"
    text = soup.get_text(" ", strip=True)
    if re.search(r"\bL@", text):
        return "L", status_map["L"]

    return None, None


def parse_name_field(name_html):
    soup = BeautifulSoup(name_html or "", "html.parser")
    anchor = soup.find("a")
    anchor_text = anchor.get_text(" ", strip=True) if anchor else extract_text(name_html)

    # Extract listed price and listing gain from the full text (span after the link)
    listed_price = listing_gain = None
    full_text = soup.get_text(" ", strip=True)
    m = re.search(r"L@([\d.]+)\s*\(([-+]?[\d.]+)%\)", full_text)
    if m:
        try:
            listed_price = float(m.group(1))
            listing_gain = float(m.group(2))
        except ValueError:
            pass

    # Detect and strip trailing exchange and board from the anchor text
    exchange = board = None
    m2 = re.search(r"\s+(BSE|NSE)\s+(SME|Mainboard|Main)\s*$", anchor_text, flags=re.IGNORECASE)
    if m2:
        exchange = m2.group(1).upper()
        board_raw = m2.group(2)
        board = "Mainboard" if board_raw.lower().startswith("main") else "SME"
        name_only = anchor_text[: m2.start()].strip()
    else:
        name_only = anchor_text.strip()

    return name_only, listed_price, listing_gain, exchange, board


def parse_gmp(html):
    txt = extract_text(html)
    m = re.search(r"₹?\b([-\d.]+)\b.*\(([-\d.]+)%\)", txt.replace(",", ""))
    val = pct = None
    if m:
        try:
            val, pct = float(m.group(1)), float(m.group(2))
        except ValueError:
            pass
    return val, pct


def parse_est_listing(html):
    return parse_gmp(html)


def parse_fire_rating(html):
    soup = BeautifulSoup(html or "", "html.parser")
    # Count actual fire emojis in the text content
    text = soup.get_text("", strip=True)
    count = text.count("🔥")

    # If none found, try to count HTML entities (e.g., &#128293;)
    if count == 0:
        raw = str(html) if html else ""
        count = raw.count("&#128293;")

    # Never assume a default; allow 0 if truly none
    emoji = "🔥" * count if count > 0 else ""
    return emoji, count



def fetch_and_save():
    url = get_api_url()
    print(f"Fetching data from: {url}")
    res = requests.get(url)
    res.raise_for_status()
    data = res.json().get("reportTableData", [])

    result = []
    for item in data:
        name_raw = item.get("Name", "")
        name, listed_price, listing_gain, exchange, board = parse_name_field(name_raw)
        status_code, status_formatted = extract_status(name_raw)
        gmp_val, gmp_pct = parse_gmp(item.get("GMP", ""))
        est_price, est_pct = parse_est_listing(item.get("Est Listing", ""))
        fire_emoji, fire_count = parse_fire_rating(item.get("Fire Rating", ""))

        ipo = {
            "ipoId": item.get("~id"),
            "apiCompanyName": name,
            "apiExchange": exchange,
            "apiBoard": board,
            "apiIpoStatus": status_code,
            "apiIpoStatusFormatted": status_formatted,
            "apiListedPrice": listed_price,
            "apiListingGain": listing_gain,
            "apiGmpValue": gmp_val,
            "apiGmpPercent": gmp_pct,
            "apiFireRating": fire_emoji,
            "apiFireRatingCount": fire_count,
            "apiSubscription": extract_text(item.get("Sub", "")),
            "apiPrice": float(item.get("Price")) if item.get("Price", "").replace(".", "").isdigit() else None,
            "apiEstimatedListingPrice": est_price,
            "apiEstimatedListingPercent": est_pct,
            "apiIssueSize": extract_text(item.get("IPO Size", "")),
            "apiLot": extract_text(item.get("Lot", "")),
            "apiPe": float(item.get("~P/E")) if item.get("~P/E", "").replace(".", "").replace("-", "").isdigit() else None,
            "apiIssueOpenDate": extract_text(item.get("~Srt_Open", "")),
            "apiIssueCloseDate": extract_text(item.get("~Srt_Close", "")),
            "apiBoaDate": extract_text(item.get("~Srt_BoA_Dt", "")),
            "apiListingAt": extract_text(item.get("~Str_Listing", "")),
            "apiUrl": "https://www.investorgain.com" + item.get("~urlrewrite_folder_name", ""),
            "apiIpoCategory": item.get("~IPO_Category"),
        }
        result.append(ipo)

    filename = "new_api_json_data.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(result)} records to '{filename}'")


if __name__ == "__main__":
    fetch_and_save()
