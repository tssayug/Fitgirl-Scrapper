import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import os
import json
import time
import random
import re
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "https://fitgirl-repacks.site"
INDEX_URL = f"{BASE_URL}/all-my-repacks-a-z/"

OUTPUT_CSV = "fitgirl_ALL_REPACKS.csv"
CHECKPOINT_FILE = "fitgirl_checkpoint.json"
FAILED_FILE = "fitgirl_failed_pages.csv"

MIN_DELAY = 1.5
MAX_DELAY = 3.0

MAX_RETRIES = 3

REQUEST_TIMEOUT = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}

session = requests.Session()
session.headers.update(HEADERS)


# ============================================================
# CSV FIELDS
# ============================================================

FIELDS = [
    "Game",
    "Genres/Tags",
    "Companies",
    "Languages",
    "Original Size",
    "Repack Size",
    "URL"
]

FAILED_FIELDS = [
    "URL",
    "Game",
    "Error",
    "Time"
]


# ============================================================
# HTTP
# ============================================================

def get_page(url):

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            response = session.get(
                url,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            return response.text

        except Exception as e:

            print(
                f"    Request failed "
                f"({attempt}/{MAX_RETRIES}): {e}"
            )

            if attempt < MAX_RETRIES:

                time.sleep(
                    3 * attempt
                )

    return None


def polite_delay():

    time.sleep(
        random.uniform(
            MIN_DELAY,
            MAX_DELAY
        )
    )


# ============================================================
# CLEAN TEXT
# ============================================================

def clean(text):

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


# ============================================================
# NORMALIZE URL
# ============================================================

def normalize_url(url):

    url = urljoin(
        BASE_URL,
        url
    )

    # Remove fragments
    url = url.split("#")[0]

    # Remove trailing slash difference
    if url.endswith("/"):
        url = url[:-1]

    return url


# ============================================================
# CHECKPOINT
# ============================================================

def load_checkpoint():

    if not os.path.exists(
        CHECKPOINT_FILE
    ):

        return {
            "completed_urls": [],
            "failed_urls": [],
            "last_index_page": 0,
            "started": datetime.now().isoformat()
        }

    try:

        with open(
            CHECKPOINT_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        print(
            "WARNING: Checkpoint could not be read."
        )

        return {
            "completed_urls": [],
            "failed_urls": [],
            "last_index_page": 0,
            "started": datetime.now().isoformat()
        }


def save_checkpoint(
    completed_urls,
    failed_urls,
    last_index_page
):

    data = {
        "completed_urls": list(
            completed_urls
        ),
        "failed_urls": list(
            failed_urls
        ),
        "last_index_page": last_index_page,
        "updated": datetime.now().isoformat()
    }

    temp_file = (
        CHECKPOINT_FILE
        + ".tmp"
    )

    with open(
        temp_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=2
        )

    os.replace(
        temp_file,
        CHECKPOINT_FILE
    )


# ============================================================
# CSV INITIALIZATION
# ============================================================

def initialize_csv():

    if os.path.exists(
        OUTPUT_CSV
    ):

        return

    with open(
        OUTPUT_CSV,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=FIELDS
        )

        writer.writeheader()


def initialize_failed_csv():

    if os.path.exists(
        FAILED_FILE
    ):

        return

    with open(
        FAILED_FILE,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=FAILED_FIELDS
        )

        writer.writeheader()


def append_result(result):

    with open(
        OUTPUT_CSV,
        "a",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=FIELDS
        )

        writer.writerow(
            result
        )


def append_failed(
    url,
    game,
    error
):

    with open(
        FAILED_FILE,
        "a",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=FAILED_FIELDS
        )

        writer.writerow({
            "URL": url,
            "Game": game,
            "Error": error,
            "Time": datetime.now().isoformat()
        })


# ============================================================
# A-Z CATALOGUE
# ============================================================

def get_index_url(page):

    if page == 1:

        return INDEX_URL

    return (
        f"{INDEX_URL}"
        f"?lcp_page0={page}"
    )


def extract_games_from_index(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    catalogue = soup.select_one(
        "#lcp_instance_0"
    )

    if catalogue is None:

        return []

    games = []

    for item in catalogue.find_all(
        "li",
        recursive=False
    ):

        link = item.find(
            "a",
            href=True,
            recursive=False
        )

        if not link:
            continue

        title = clean(
            link.get_text(
                " ",
                strip=True
            )
        )

        url = normalize_url(
            link["href"]
        )

        if not title or not url:
            continue

        games.append({
            "Game": title,
            "URL": url
        })

    return games


# ============================================================
# FIND NEXT INDEX PAGE
# ============================================================

def has_more_index_pages(
    html,
    current_page,
    games_found
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    catalogue = soup.select_one(
        "#lcp_instance_0"
    )

    if catalogue is None:
        return False

    # --------------------------------------------------------
    # Look for pagination links associated with the catalogue.
    # --------------------------------------------------------

    links = catalogue.find_all(
        "a",
        href=True
    )

    for link in links:

        text = clean(
            link.get_text(
                " ",
                strip=True
            )
        ).lower()

        href = link["href"]

        # Common "next" forms
        if text in [
            "next",
            "next page",
            "older posts",
            ">"
        ]:

            return True

        # If the URL contains a later page number
        match = re.search(
            r"lcp_page0=(\d+)",
            href
        )

        if match:

            page_number = int(
                match.group(1)
            )

            if page_number > current_page:
                return True

    # --------------------------------------------------------
    # Fallback:
    #
    # If this page contained a full 50-game batch,
    # try the next page.
    #
    # If fewer than 50, this is probably the final page.
    # --------------------------------------------------------

    if len(games_found) >= 50:
        return True

    return False


# ============================================================
# STATS BLOCK
# ============================================================

def get_article(soup):

    article = soup.select_one(
        "article"
    )

    if article:
        return article

    return soup


# ============================================================
# FIND EXACT STATS LINE
# ============================================================

def find_stats_element(
    article,
    label
):

    target = label.lower()

    # --------------------------------------------------------
    # Search text nodes that contain the exact label.
    # --------------------------------------------------------

    for element in article.find_all(
        string=re.compile(
            rf"^\s*{re.escape(label)}\s*:",
            re.IGNORECASE
        )
    ):

        parent = element.parent

        if parent:
            return parent

    return None


# ============================================================
# GENRES / TAGS
# ============================================================

def extract_genres(article):

    element = find_stats_element(
        article,
        "Genres/Tags"
    )

    if not element:
        return ""

    # --------------------------------------------------------
    # The important part:
    #
    # Collect ALL <a> tags belonging to this exact
    # Genres/Tags field.
    # --------------------------------------------------------

    links = element.find_all(
        "a"
    )

    genres = []

    for link in links:

        value = clean(
            link.get_text(
                " ",
                strip=True
            )
        )

        if value:
            genres.append(value)

    # If the structure is split over the parent,
    # inspect the closest containing element.
    if not genres:

        parent = element.parent

        if parent:

            links = parent.find_all(
                "a"
            )

            for link in links:

                value = clean(
                    link.get_text(
                        " ",
                        strip=True
                    )
                )

                if value:
                    genres.append(value)

    return ", ".join(
        dict.fromkeys(
            genres
        )
    )


# ============================================================
# COMPANIES
# ============================================================

def extract_companies(article):

    element = find_stats_element(
        article,
        "Companies"
    )

    if not element:
        return ""

    # Usually bold text rather than links.
    text = clean(
        element.get_text(
            " ",
            strip=True
        )
    )

    text = re.sub(
        r"^\s*Companies\s*:\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    return clean(text)


# ============================================================
# LANGUAGES
# ============================================================

def extract_languages(article):

    element = find_stats_element(
        article,
        "Languages"
    )

    if not element:
        return ""

    text = clean(
        element.get_text(
            " ",
            strip=True
        )
    )

    text = re.sub(
        r"^\s*Languages\s*:\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    return clean(text)


# ============================================================
# SIZE
# ============================================================

def extract_size(
    article,
    label
):

    element = find_stats_element(
        article,
        label
    )

    if not element:
        return ""

    text = clean(
        element.get_text(
            " ",
            strip=True
        )
    )

    text = re.sub(
        rf"^\s*{re.escape(label)}\s*:\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    match = re.search(
        r"\b[\d.,]+\s*(?:KB|MB|GB|TB)\b",
        text,
        flags=re.IGNORECASE
    )

    if match:

        return clean(
            match.group(0)
        )

    return clean(text)


# ============================================================
# INDIVIDUAL GAME PAGE
# ============================================================

def scrape_game(game):

    html = get_page(
        game["URL"]
    )

    if not html:

        raise RuntimeError(
            "Page download failed"
        )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    article = get_article(
        soup
    )

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title_element = article.select_one(
        "h1.entry-title"
    )

    if not title_element:

        title_element = article.select_one(
            "h1"
        )

    if title_element:

        title = clean(
            title_element.get_text(
                " ",
                strip=True
            )
        )

    else:

        title = game["Game"]


    # --------------------------------------------------------
    # EXACT REQUIRED FIELDS
    # --------------------------------------------------------

    genres = extract_genres(
        article
    )

    companies = extract_companies(
        article
    )

    languages = extract_languages(
        article
    )

    original_size = extract_size(
        article,
        "Original Size"
    )

    repack_size = extract_size(
        article,
        "Repack Size"
    )


    return {
        "Game": title,
        "Genres/Tags": genres,
        "Companies": companies,
        "Languages": languages,
        "Original Size": original_size,
        "Repack Size": repack_size,
        "URL": game["URL"]
    }


# ============================================================
# VALIDATION
# ============================================================

def validate_result(result):

    problems = []

    if not result["Game"]:
        problems.append(
            "missing game title"
        )

    if not result["URL"]:
        problems.append(
            "missing URL"
        )

    if not result["Original Size"]:
        problems.append(
            "missing original size"
        )

    if not result["Repack Size"]:
        problems.append(
            "missing repack size"
        )

    if not result["Languages"]:
        problems.append(
            "missing languages"
        )

    return problems


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 75)
    print("FITGIRL CATALOGUE SCRAPER V4")
    print("=" * 75)
    print()

    initialize_csv()
    initialize_failed_csv()

    checkpoint = load_checkpoint()

    completed_urls = set(
        checkpoint.get(
            "completed_urls",
            []
        )
    )

    failed_urls = set(
        checkpoint.get(
            "failed_urls",
            []
        )
    )

    last_index_page = int(
        checkpoint.get(
            "last_index_page",
            0
        )
    )


    print(
        f"Previously completed: "
        f"{len(completed_urls)}"
    )

    print(
        f"Previously failed: "
        f"{len(failed_urls)}"
    )

    print()


    # ========================================================
    # PHASE 1 — DISCOVER ALL GAME URLS
    # ========================================================

    print("=" * 75)
    print("PHASE 1 — DISCOVERING ENTIRE A-Z CATALOGUE")
    print("=" * 75)
    print()


    all_games = {}
    page = 1

    while True:

        print(
            f"[INDEX PAGE {page}]"
        )

        url = get_index_url(
            page
        )

        html = get_page(
            url
        )

        if not html:

            print(
                "  Could not download index page."
            )

            print(
                "  Stopping catalogue discovery."
            )

            break


        games = extract_games_from_index(
            html
        )


        print(
            f"  Games found: {len(games)}"
        )


        if not games:

            print(
                "  No games found."
            )

            print(
                "  End of catalogue reached."
            )

            break


        new_games = 0

        for game in games:

            game_url = game["URL"]

            if game_url not in all_games:

                all_games[
                    game_url
                ] = game

                new_games += 1


        print(
            f"  New unique games: {new_games}"
        )

        print(
            f"  Total unique games: "
            f"{len(all_games)}"
        )


        # ----------------------------------------------------
        # Determine whether another page exists
        # ----------------------------------------------------

        if not has_more_index_pages(
            html,
            page,
            games
        ):

            print()
            print(
                "No further catalogue page detected."
            )

            break


        page += 1

        polite_delay()


    # ========================================================
    # SAVE DISCOVERY CHECKPOINT
    # ========================================================

    save_checkpoint(
        completed_urls,
        failed_urls,
        page
    )


    print()
    print("=" * 75)
    print(
        f"CATALOGUE DISCOVERY COMPLETE"
    )
    print(
        f"TOTAL UNIQUE GAMES: {len(all_games)}"
    )
    print("=" * 75)
    print()


    # ========================================================
    # PHASE 2 — SCRAPE INDIVIDUAL GAME PAGES
    # ========================================================

    games = list(
        all_games.values()
    )

    total = len(games)

    remaining = [
        game
        for game in games
        if game["URL"]
        not in completed_urls
    ]


    print(
        f"Already completed: {len(completed_urls)}"
    )

    print(
        f"Remaining: {len(remaining)}"
    )

    print()


    if not remaining:

        print(
            "Everything has already been scraped."
        )

        return


    start_time = time.time()

    successful_this_run = 0
    failed_this_run = 0


    for number, game in enumerate(
        remaining,
        1
    ):

        overall_number = (
            total
            - len(remaining)
            + number
        )

        print()
        print("-" * 75)

        print(
            f"[{number}/{len(remaining)}] "
            f"Overall: {overall_number}/{total}"
        )

        print(
            f"Game: {game['Game']}"
        )

        print(
            f"URL: {game['URL']}"
        )


        try:

            result = scrape_game(
                game
            )


            problems = validate_result(
                result
            )


            # ------------------------------------------------
            # Show extracted data
            # ------------------------------------------------

            print(
                f"  Genres:    "
                f"{result['Genres/Tags']}"
            )

            print(
                f"  Companies: "
                f"{result['Companies']}"
            )

            print(
                f"  Languages: "
                f"{result['Languages']}"
            )

            print(
                f"  Original:  "
                f"{result['Original Size']}"
            )

            print(
                f"  Repack:    "
                f"{result['Repack Size']}"
            )


            if problems:

                print(
                    "  WARNING: "
                    + ", ".join(problems)
                )


            # ------------------------------------------------
            # SAVE IMMEDIATELY
            # ------------------------------------------------

            append_result(
                result
            )

            completed_urls.add(
                game["URL"]
            )

            successful_this_run += 1


            # ------------------------------------------------
            # Checkpoint after EVERY game
            # ------------------------------------------------

            save_checkpoint(
                completed_urls,
                failed_urls,
                page
            )


        except Exception as e:

            error = str(e)

            print(
                f"  FAILED: {error}"
            )

            append_failed(
                game["URL"],
                game["Game"],
                error
            )

            failed_urls.add(
                game["URL"]
            )

            failed_this_run += 1


            save_checkpoint(
                completed_urls,
                failed_urls,
                page
            )


        # ----------------------------------------------------
        # Progress estimate
        # ----------------------------------------------------

        elapsed = (
            time.time()
            - start_time
        )

        if successful_this_run > 0:

            average = (
                elapsed
                / successful_this_run
            )

            remaining_count = (
                len(remaining)
                - number
            )

            eta_seconds = (
                average
                * remaining_count
            )

            eta_minutes = (
                eta_seconds
                / 60
            )

            print(
                f"  Approx. remaining: "
                f"{eta_minutes:.1f} minutes"
            )


        polite_delay()


    # ========================================================
    # FINAL REPORT
    # ========================================================

    print()
    print()
    print("=" * 75)
    print("SCRAPE COMPLETE")
    print("=" * 75)

    print(
        f"Successful this run: "
        f"{successful_this_run}"
    )

    print(
        f"Failed this run: "
        f"{failed_this_run}"
    )

    print(
        f"Total completed: "
        f"{len(completed_urls)}"
    )

    print()
    print(
        f"Main CSV: "
        f"{OUTPUT_CSV}"
    )

    print(
        f"Failed pages: "
        f"{FAILED_FILE}"
    )

    print(
        f"Checkpoint: "
        f"{CHECKPOINT_FILE}"
    )

    print()
    print(
        "You can safely stop the script at any time."
    )

    print(
        "Run it again to resume from the checkpoint."
    )

    print("=" * 75)


if __name__ == "__main__":
    main()