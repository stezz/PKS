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

username = "user"
password = "password"

pks = PksLive(username, password)

# get your customer
customer = pks.get_customer_info()
# Get your contract
contract = customer.contracts[0]

# Get the info about your invoicing (with VAT)
for period in contract.invoicing_periods:
    fixed_price = period.get_with_vat(period.average_fixed_price)
    spot_price = period.get_with_vat(period.average_spot_price)
    weighted_spot_price = period.get_with_vat(period.weighted_spot_price)
    total_fixed_cost = period.get_with_vat(period.total_fixed_cost)
    total_spot_cost = period.get_with_vat(period.total_spot_cost)
    total_weighted_spot_cost = period.get_with_vat(period.total_weighted_spot_cost)
```
