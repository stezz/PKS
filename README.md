# PksLive

This is a simple python object that allows you to connect to [PKS Live](https://live.pks.fi) site and interact with its APIs

## Installation

To install and set up the project, follow these steps:

```shell
git clone https://github.com/stezz/pkslive.git
pip install poetry
cd
poetry install
```

## Usage

```python
from pks_api import PksLive
from pprint import pprint
import aiohttp, asyncio

username = "user"
password = "password"


async def main():
    pks = PksLive(username, password)

    customer = pks.get_customer_info()
    contract = customer.contracts[0]
    total_spend_fixed = 0
    total_spend_spot = 0
    periods = await contract.get_invoicing_periods()
    for period in periods:
        fixed_price = period.get_with_vat(period.average_fixed_price)
        spot_price = period.get_with_vat(period.average_spot_price)
        weighted_spot_price = period.get_with_vat(period.weighted_spot_price)
        total_fixed_cost = period.get_with_vat(period.total_fixed_cost)
        total_spot_cost = period.get_with_vat(period.total_spot_cost)
        total_weighted_spot_cost = period.get_with_vat(period.total_weighted_spot_cost)
        if total_fixed_cost > 0:
            total_spend_fixed += total_fixed_cost
            total_spend_spot += total_spot_cost
        period_start = datetime.strftime(period.start, "%Y-%m-%d")
        period_stop = datetime.strftime(period.stop, "%Y-%m-%d")


# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
```
