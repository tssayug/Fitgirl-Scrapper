# FitGirl Repack Catalogue

A structured catalogue of game metadata collected from the public FitGirl Repacks A–Z catalogue.

The project is intended to make the large catalogue easier to search, filter, analyze, and use for personal game discovery.

## Dataset

The current dataset contains **7,198 successfully scraped game entries**.

Each entry contains:

- **Game** — Game title
- **Genres/Tags** — Genres and tags listed on the game page
- **Companies** — Developer/publisher information when available
- **Languages** — Languages supported by the repack
- **Original Size** — Original game size
- **Repack Size** — Size of the repack
- **URL** — Link to the corresponding game page

## Features

- Automatically discovers catalogue pages
- Follows A–Z catalogue pagination
- Collects unique game URLs
- Removes duplicate entries
- Extracts metadata from individual game pages
- Saves results incrementally
- Supports checkpoint-based resuming
- Records pages that fail to scrape
- Exports the collected data as CSV

## Repository Structure

```text
fitgirl-catalogue/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── scraper/
│   └── fitgirl_scraper.py
│
└── data/
    ├── fitgirl_ALL_REPACKS.csv
    └── fitgirl_failed_pages.csv
```

## Requirements

- Python 3.9+
- Internet connection

Install the required dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

Run the scraper with:

```bash
python scraper/fitgirl_scraper.py
```

The scraper will:

1. Discover the available catalogue pages.
2. Collect unique game URLs.
3. Visit individual game pages.
4. Extract the requested metadata.
5. Save the results to the CSV file.
6. Update the checkpoint after successful entries.
7. Record failed pages separately.

## Checkpoint & Resume

The scraper uses a checkpoint system to prevent completed work from being lost.

If the script is interrupted, it can be run again and will continue from the saved checkpoint rather than starting the entire scrape again.

The checkpoint file is:

```text
fitgirl_checkpoint.json
```

This file is local scraper state and is not required for using the completed dataset.

## Output Files

### `fitgirl_ALL_REPACKS.csv`

The main dataset containing successfully scraped game metadata.

### `fitgirl_failed_pages.csv`

Contains pages that could not be successfully scraped during the run.

### `fitgirl_checkpoint.json`

Stores the scraper's progress and allows interrupted runs to resume.

## Example Dataset

| Game | Genres/Tags | Companies | Languages | Original Size | Repack Size |
|---|---|---|---|---:|---:|
| Example Game | Action, Adventure, 3D | Example Studio | ENG/MULTI5 | 20 GB | 12 GB |

## Possible Uses

The dataset can be used for:

- Game catalogue exploration
- Genre and tag analysis
- Game size comparisons
- Language filtering
- Dataset analysis
- Building search and filtering tools
- Personal game-library planning
- Learning web scraping and data processing

## Disclaimer

This project is a **metadata/catalogue project**.

It does not contain, distribute, or host game files, installers, cracks, or other copyrighted game content.

This project is not affiliated with, endorsed by, or sponsored by FitGirl Repacks or any game publisher or developer.

All game names, trademarks, and related intellectual property belong to their respective owners.

Users are responsible for complying with applicable laws and the terms and policies of the websites they access.

## Source

The catalogue metadata was collected from the publicly accessible FitGirl Repacks A–Z catalogue:

https://fitgirl-repacks.site/all-my-repacks-a-z/

Please respect the source website's policies and avoid excessive request rates when running the scraper.

## License

The scraper code may be reused and modified according to the license included with this repository.

The dataset consists of metadata collected from a third-party website. Users should verify applicable rights and restrictions before redistributing or using the dataset commercially.

---

**Status:** Complete

**Successfully scraped:** 7,198 games

**Failed pages:** 1
