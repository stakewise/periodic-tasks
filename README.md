# Stakewise periodic tasks

Collection of scripts that should be run periodically.

List of scripts:

* `src/update_price.py`
* `src/update_ltv.py` - updates user having maximum LTV in given vault. Users are stored in `VaultUserLtvTracker` contract.

## Setup

1. Install [poetry](https://python-poetry.org/)
2. Install dependencies: `poetry install`
3. `cp .env.example .env`
4. Fill .env file with appropriate values

## Run

1. `poetry shell`
2. `export PYTHONPATH=.`
3. `python <script-path>`
