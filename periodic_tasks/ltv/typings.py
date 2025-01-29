from dataclasses import dataclass

from web3.types import ChecksumAddress

from periodic_tasks.common.typings import HarvestParams


@dataclass
class VaultMaxLtvUser:
    address: ChecksumAddress
    vault: ChecksumAddress
    harvest_params: HarvestParams | None
