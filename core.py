import json
import requests
from pycoingecko import CoinGeckoAPI

class Wallet_Info():
    
    #Main Constructor
    def __init__(self, wallet, currency="usd"):
        self.wallet = wallet
        self.currency = currency
        self.Wallet_Info()

    
    DATA_TRANSACTIONS = []
    cg = CoinGeckoAPI()
    
    #Secondary Constructor Method
    def Wallet_Info(self):
        self.getWalletTransactions()
        print(self.DATA_TRANSACTIONS)
    
    
    def getWalletTransactions(self):
        url = "https://algoindexer.algoexplorerapi.io/v2/transactions"
        parameters = {'address': self.wallet, 'asset-id': 27165954, 'limit': 1000}
        response = requests.get(url, params=parameters)
        json_body = response.json()
        transaction_body = json_body["transactions"]


        for transaction in transaction_body:
            data = {}
            data["tx"] = str(transaction["id"])
            data["amount"] = float(transaction["asset-transfer-transaction"]["amount"] / 1000000)
            data["timestamp"] = int(transaction["round-time"])
            if(data["amount"] <= 0):
                continue
            data["current_price"] = self.getCurrentPrice(data["amount"])
            self.DATA_TRANSACTIONS.append(data)

    def getCurrentPrice(self, amount):
        value = self.cg.get_price(ids='planetwatch', vs_currencies=self.currency)["planetwatch"][self.currency]
        return amount * value

    def getPriceFromDate(self, amount, date):
        pass

        
    

obj = Wallet_Info("YXVQYXUUD3PGFBX3P7SSB5RRMJX22NKVSMTZVCSHEZVH5L27JUZNEURBMU", "chf")