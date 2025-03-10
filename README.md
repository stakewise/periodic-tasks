# Stakewise periodic tasks

Collection of scripts that should be run periodically.

List of scripts:

* `periodic_tasks/update_price.py` - calls the function on the mainnet that updates the osETH-to-ETH price on the L2 network, i.e., the target network.
* `periodic_tasks/update_ltv.py` - updates user having maximum LTV in given vault. Users are stored in `VaultUserLtvTracker` contract.
* `periodic_tasks/force_exit.py` - monitor leverage positions and trigger exits/claims for those that approach the liquidation threshold.
* `periodic_tasks/infinity_pools.py` - convert the vault balance into pool tokens and distribute the converted amount to the pool shareholders.

## Setup

1. Install [poetry](https://python-poetry.org/)
2. Install dependencies: `poetry install`
3. `cp .env.example .env`
4. Fill .env file with appropriate values

## Run

1. `poetry shell`
2. `export PYTHONPATH=.`
3. `python <script-path>`
