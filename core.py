import json
import requests
from pycoingecko import CoinGeckoAPI

class Wallet_Info():
    
    #Main Constructor
    def __init__(self, wallet, currency="usd"):
        self.wallet = wallet
        self.currency = currency
        self.Wallet_Info() #Call Secondary "Constructor"

    
    DATA_TRANSACTIONS = []
    CURRENT_VALUE_PLANET = 0.0
    CURRENT_BALANCE = 0.0
    CURRENT_BALANCE_VALUE = 0.0
    PREVIOUS_BALANCE_VALUE = 0.0
    BALANCE_DIFFERENCE = 0.0

    cg = CoinGeckoAPI()
    
    #Secondary "Constructor" Method
    def Wallet_Info(self):
        self.CURRENT_VALUE_PLANET = self.getCurrentPrice(1)
        self.CURRENT_BALANCE = self.getWalletBalance()
        self.getWalletTransactions()
        self.BALANCE_DIFFERENCE = self.CURRENT_BALANCE_VALUE - self.PREVIOUS_BALANCE_VALUE
    
    def getWalletBalance(self):
        url = f"https://algoindexer.algoexplorerapi.io/v2/accounts/{self.wallet}?include-all=true"
        response = requests.get(url)
        json_body = response.json()
        account_body = json_body["account"]

        for asset in account_body["assets"]:
            if(int(asset["asset-id"]) == 27165954):
                return int(asset["amount"]) / 1000000
    
    def getWalletTransactions(self):
        url = "https://algoindexer.algoexplorerapi.io/v2/transactions"
        parameters = {'address': self.wallet, 'asset-id': 27165954, 'limit': 1000}
        response = requests.get(url, params=parameters)
        json_body = response.json()
        transaction_body = json_body["transactions"]


        for transaction in transaction_body:
            data = {}

            data["amount"] = float(transaction["asset-transfer-transaction"]["amount"] / 1000000)
            if(int(data["amount"]) == 0):
                continue
            data["tx"] = str(transaction["id"])
            data["timestamp"] = int(transaction["round-time"])
            data["current_price"] = self.getCurrentPrice(data["amount"])
            data["previous_price"] = self.getPriceFromDate(data["amount"], data["timestamp"])

            difference = self.getPriceDifference(data["current_price"], data["previous_price"])
            if(difference > 0):
                data["price_difference"] = "+" + str(difference)
            else:
                data["price_difference"] = str(difference)
            
            self.DATA_TRANSACTIONS.append(data)

        for y in self.DATA_TRANSACTIONS:
            self.CURRENT_BALANCE_VALUE += float(y["current_price"])
            self.PREVIOUS_BALANCE_VALUE += float(y["previous_price"])

    def getCurrentPrice(self, amount):
        value = self.cg.get_price(ids='planetwatch', vs_currencies=self.currency)["planetwatch"][self.currency]
        return amount * value

    def getPriceFromDate(self, amount, date):
        json_body = self.cg.get_coin_market_chart_range_by_id(id="planetwatch", vs_currency=self.currency, from_timestamp=(date - 500), to_timestamp=(date + 1000))
        for x in json_body["prices"]:
            time_unix = x[0]
            value = x[1]

            if(time_unix < date):
                continue
            else:
                return amount * value

    def getPriceDifference(self, price_now, previous_price):
        return price_now - previous_price