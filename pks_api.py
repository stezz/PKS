import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
from zoneinfo import ZoneInfo
import pandas as pd

class PksLive:
    """PKS Live API client.

    :param username: PKS Live username
    :param password: PKS Live password
    :type username: str
    :type password: str
    :return: PKS Live API client
    :rtype: PksLive

    Usage:
    pks = PksLive(username, password)
    """
    def __init__(self, username, password):
        self.api_url = "https://live.pks.fi/Api"
        self.username = username
        self.password = password
        self.login_url = "https://oma.pks.fi/eServices/Online/Login"
        self.live_login_url = "https://oma.pks.fi/eServices/Online/MoveToPKSLiveUser"
        self.session = self.login(username, password)


    def login(self, username, password):
        """Login to PKS Live API.
        :param username: PKS Live username
        :param password: PKS Live password
        :type username: str
        :type password: str
        :return: requests session
        :rtype: requests.Session
        """
        session = requests.Session()
        response = session.get(self.login_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        token = soup.find("input", {"name": "__RequestVerificationToken"})['value']
        payload = {
            "__RequestVerificationToken": token,
            "UserName": username,
            "Password": password
        }
        response = session.post(self.login_url, data=payload)

        if response.status_code == 200:
            print("Login successful")
            response = session.get(self.live_login_url)
            return session
        else:
            print("Login failed")
            return None



    def get_customer_info(self):
        """Get customer info.

        :return: Customer object
        :rtype: Customer
        """
        try:
            response = self.session.get(f"{self.api_url}/Customer")
            response.raise_for_status()
            data = response.json()[0]
            return Customer(parent=self, **data)
        except requests.RequestException as e:
            print(f"Error: {e}")
            return None

    def get_contract_info(self, id):
        """Get contract info.

        :param id: Contract ID
        :type id: int
        :return: Contract object
        :rtype: Contract
        """
        try:
            response = self.session.get(f"{self.api_url}/Customer/Contracts/{id}")
            response.raise_for_status()  # Raises stored HTTPError, if one occurred.
            data = response.json()
            # Assuming there's a Contract class defined similarly to Customer
            return data[0]
        except requests.RequestException as e:
            print(f"Error: {e}")
            return None

class Customer:
    """Customer object.

    :param parent: Parent object
    :type parent: PksLive
    :param kwargs: Customer data
    :type kwargs: dict
    :return: Customer object
    :rtype: Customer
    """
    def __init__(self, parent, **kwargs):
        self.address = kwargs.get('Address', None)
        self._contracts = None
        self._contracts_data = kwargs.get('Contracts', []) or []
        self.id = kwargs.get('Id', None)
        self.customercode = kwargs.get('CustomerCode', None)
        self.firstname = kwargs.get('FirstName', None)
        self.lastname = kwargs.get('LastName', None)
        self.companyname = kwargs.get('CompanyName', None)
        self.email = kwargs.get('Email', None)
        self.phone = kwargs.get('Phone', None)
        self.identifier = kwargs.get('Identifier', None)
        self.addressid = kwargs.get('AddressId', None)
        self.maincustomerid = kwargs.get('MainCustomerId', None)
        self.rawdata = kwargs
        self.parent = parent
        self.api_url = self.parent.api_url
        self.session = self.parent.session

    @property
    def contracts(self):
        """Get customer contracts.

        :param parent: Parent object
        :type parent: Customer
        :return: List of Contract objects
        :rtype: list
        """
        if self._contracts:
            return self._contracts
        self._contracts = [Contract(parent=self, **data) for data in self._contracts_data]
        return self._contracts

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id} - {self.firstname} {self.lastname})"


class Contract:
    """Contract object.

    :param parent: Parent object
    :type parent: Customer
    :param kwargs: Contract data
    :type kwargs: dict
    :return: Contract object
    :rtype: Contract
    """
    def __init__(self, parent, **kwargs):
        self.id = kwargs.get('Id', None)
        self.meteringpointid = kwargs.get('MeteringPointId', None)
        self.meteringpoint = kwargs.get('MeteringPoint', None)
        self.created = kwargs.get('Created', None)
        self.contractcode = kwargs.get('ContractCode', None)
        self.start = kwargs.get('Start', None)
        self.stop = kwargs.get('Stop', None)
        self.product = kwargs.get('Product', None)
        self.parent = parent
        self.api_url = self.parent.api_url
        self.session = self.parent.session
        self.customer = self.parent
        self._invoicing_periods = None
        self.rawdata = kwargs

    @property
    def invoicing_periods(self):
        """Get invoicing periods for the contract.

        :return: List of InvoicingPeriod objects
        :rtype: list
        """
        if self._invoicing_periods:
            return self._invoicing_periods
        try:
            url = f"{self.api_url}/Periods/InvoicingPeriod/Available"
            response = self.session.get(url)
            response.raise_for_status()
            periods_data = response.json()
            self._invoicing_periods = [InvoicingPeriod(parent=self, **data) for data in periods_data]
            return self._invoicing_periods
        except requests.RequestException as e:
            print(f'ERROR: {e}')
            return None


    def __repr__(self):
        return f"{self.__class__.__name__}({self.id})"


class InvoicingPeriod:
    """InvoicingPeriod object.

    :param parent: Parent object
    :type parent: Contract
    :param kwargs: InvoicingPeriod data
    :type kwargs: dict
    :return: InvoicingPeriod object
    :rtype: InvoicingPeriod
    """
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.api_url = self.parent.api_url
        self.session = self.parent.session
        self.id = kwargs.get('Id', None)
        self.description = kwargs.get('Description', None)
        self.time_zone = ZoneInfo("Europe/Helsinki")
        self.start = datetime.strptime(kwargs.get('Start', None),
                    "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=ZoneInfo("UTC")).astimezone(self.time_zone)
        self.stop = datetime.strptime(kwargs.get('Stop', None),
                    "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=ZoneInfo("UTC")).astimezone(self.time_zone)
        self._hourly_data = None
        self.rawdata = kwargs
        self._average_spot_price = None
        self._average_fixed_price = None
        self._profile_price = None
        self._delivery_price = None
        self._weighted_spot_price = None
        self._total_spot_price = None
        self._total_weighted_spot_price = None
        self._total_fixed_price = None
        self._total_spot_cost = None
        self._total_fixed_cost = None
        self._total_weighted_spot_cost = None
        self._total_consumption = None
        self._vat_percentage = None

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id} {self.description})"

    @property
    def vat_percentage(self):
        """Get the VAT percentage for the invoicing period.

        :return: VAT percentage
        :rtype: float
        """
        if self._vat_percentage:
            return self._vat_percentage
        try:
            start_day = self.start.strftime("%Y-%m-%d")
            url = f"{self.api_url}/Periods/VatPercent/{start_day}"
            response = self.session.get(url)
            response.raise_for_status()
            self._vat_percentage = response.json()
            return self._vat_percentage
        except requests.RequestException as e:
            print(f'ERROR: {e}')
            return None

    @property
    def total_consumption(self):
        """Get the total consumption for the invoicing period.

        :return: Total consumption
        :rtype: float
        """
        if self._total_consumption:
            return self._total_consumption
        if self.hourly_data is not None:
            return self.hourly_data['Consumption'].sum() * 1000

    @property
    def total_weighted_spot_price(self):
        """Get the total weighted spot price for the invoicing period.

        :return: Total weighted spot price
        :rtype: float
        """
        if self._total_spot_price:
            return self._total_spot_price
        return self.weighted_spot_price + self.delivery_price + self.profile_price

    @property
    def total_spot_price(self):
        """Get the total spot price for the invoicing period.

        :return: Total spot price
        :rtype: float
        """
        if self._total_spot_price:
            return self._total_spot_price
        return self.average_spot_price + self.delivery_price + self.profile_price

    @property
    def total_fixed_price(self):
        """Get the total fixed price for the invoicing period.

        :return: Total fixed price
        :rtype: float
        """
        if self._total_fixed_price:
            return self._total_fixed_price
        if self.average_fixed_price > 0:
            return self.average_fixed_price + self.delivery_price + self.profile_price
        else:
            return 0

    @property
    def total_spot_cost(self):
        """Get the total spot cost for the invoicing period.

        :return: Total spot cost
        :rtype: float
        """
        if self._total_spot_cost:
            return self._total_spot_cost
        return (self.total_spot_price * self.total_consumption) / 100

    @property
    def total_fixed_cost(self):
        """Get the total fixed cost for the invoicing period.

        :return: Total fixed cost
        :rtype: float
        """
        if self._total_fixed_cost:
            return self._total_fixed_cost
        return (self.total_fixed_price * self.total_consumption) / 100

    @property
    def total_weighted_spot_cost(self):
        """Get the total weighted spot cost for the invoicing period.

        :return: Total weighted spot cost
        :rtype: float
        """
        if self._total_weighted_spot_cost:
            return self._total_weighted_spot_cost
        return (self.total_weighted_spot_price * self.total_consumption) / 100

    @property
    def average_spot_price(self):
        if self._average_fixed_price:
            return self._average_fixed_price
        if self.hourly_data is not None:
            return (self.hourly_data['SpotPrice'].mean() / 10)

    @property
    def average_fixed_price(self):
        if self._average_fixed_price:
            return self._average_fixed_price
        if self.hourly_data is not None:
            return (self.hourly_data['FixedPrice'].mean() / 10)

    @property
    def profile_price(self):
        if self._profile_price:
            return self._profile_price
        if self.hourly_data is not None:
            return (self.hourly_data['ProfilePrice'].mean() / 10)

    @property
    def delivery_price(self):
        if self._delivery_price:
            return self._delivery_price
        if self.hourly_data is not None:
            return (self.hourly_data['DeliveryPrice'].mean() / 10)

    @property
    def weighted_spot_price(self):
        if self._weighted_spot_price:
            return self._weighted_spot_price
        if self.hourly_data is not None:
            total_cost = (self.hourly_data['SpotPrice'] * self.hourly_data['Consumption']).sum()
            total_consumption = self.hourly_data['Consumption'].sum()
            return (total_cost / total_consumption) / 10

    def get_with_vat(self, price):
        return price * (1 + self.vat_percentage / 100)

    @property
    def hourly_data(self):
        if self._hourly_data is not None:
            return self._hourly_data
        try:
            url = f"{self.api_url}/Customer/Invoicing/HourlyData/{self.id}/{self.parent.id}"
            response = self.session.get(url)
            response.raise_for_status()
            self._hourly_data = response.json()
            self._hourly_data = pd.DataFrame(self._hourly_data)
            return self._hourly_data
        except requests.RequestException as e:
            print(f'ERROR: {e}')
            return None

    def download_csv(self, filename=None):
        data = self.hourly_data
        if data is None or len(data) == 0:
            print("No hourly data to download.")
            return

        if not filename:
            first_timestamp = datetime.strptime(data['TimeStamp'].iloc[0], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=ZoneInfo("UTC"))
            last_timestamp = datetime.strptime(data['TimeStamp'].iloc[-1], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=ZoneInfo("UTC"))
            first_timestamp = first_timestamp.astimezone(self.time_zone)
            last_timestamp = last_timestamp.astimezone(self.time_zone)
            filename = f"HourlyData_{first_timestamp.strftime('%Y-%m-%d')}-{last_timestamp.strftime('%Y-%m-%d')}.csv"

        data.to_csv(filename, index=False)
        print(f"Hourly data successfully downloaded to {filename}.")



