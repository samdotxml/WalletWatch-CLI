from ast import arg
import requests
from pycoingecko import CoinGeckoAPI
import tabulate
from datetime import datetime
from algosdk.v2client import indexer
from time import sleep
import csv
import base64
import json
from click import progressbar as pg


#TODO Matplotlib for faster calculations
#TODO Faster Iterations


class Wallet_Info():
    
    #Main Constructor
    def __init__(self, wallet, currency, cli_args):
        self.cli_args = cli_args['args']
        self.wallet = wallet
        self.currency = str(currency).lower()
        self.Wallet_Info() #Call Secondary "Constructor"

    #Data
    DATA_TRANSACTIONS = []
    DATA_TABLE = []

    #Statistical Variables
    CURRENT_VALUE_PLANET = 0.0
    CURRENT_BALANCE = 0.0
    CURRENT_BALANCE_VALUE = 0.0
    PREVIOUS_BALANCE_VALUE = 0.0
    BALANCE_DIFFERENCE = 0.0
    CURRENCY_SYMBOL = ""
    

    cg = CoinGeckoAPI()
    
    #Secondary "Constructor" Method
    def Wallet_Info(self):
        self.CURRENCY_SYMBOL = f"[{str(self.currency).upper()}]"
        self.CURRENT_VALUE_PLANET = float(self.getCurrentPrice(1))
        self.CURRENT_BALANCE = self.getWalletBalance()
        self.getWalletTransactions()
        self.createDataTableJson()
        self.DATA_TABLE = self.createTable()
        self.printWalletTransactions()
        self.exportData()
    
    def getWalletBalance(self):
        url = f"https://algoindexer.algoexplorerapi.io/v2/accounts/{self.wallet}?include-all=true"
        response = requests.get(url)
        json_body = response.json()
        account_body = json_body["account"]

        for asset in account_body["assets"]:
            if(int(asset["asset-id"]) == 27165954):
                return int(asset["amount"]) / 1000000
    
    def getWalletTransactions(self):
        nexttoken = ""
        numtx = 1

        # create an algod client
        indexer_token = ""
        indexer_address = "https://algoindexer.algoexplorerapi.io/"
        myindexer = indexer.IndexerClient(indexer_token, indexer_address)
        transactions = []

        while numtx > 0:
            response = myindexer.search_asset_transactions(
                address=self.wallet,
                asset_id=27165954,
                min_amount=10,
                next_page=nexttoken,
                limit=1000,
            )
            transaction_page = response["transactions"]
            numtx = len(transaction_page)
            if numtx > 0:
                transactions = transactions + transaction_page
                nexttoken = response["next-token"]

        
        if(self.cli_args['verbose']):
            self.getWalletTransactionsLoop(transactions)
        else:
            with pg(transactions) as items:
                self.getWalletTransactionsLoop(items)

    
    def getWalletTransactionsLoop(self, transactions):
        index = 0
        for transaction in transactions:
            data = {}
            if(transaction["asset-transfer-transaction"]["amount"] == 0):
                continue

            if(self.cli_args['get'] in ['rewards', 'devices']):
                if transaction["sender"] not in [
                    "ZW3ISEHZUHPO7OZGMKLKIIMKVICOUDRCERI454I3DB2BH52HGLSO67W754",
                    "X2W76H7A57BNGV6UQNMYQHCFOK4BI4DE6AG7V7BIGIYSNGCPBO44JXRMHA",
                    ]:
                    continue

            if(transaction['sender'] == self.wallet):
                data["amount"] = float(transaction["asset-transfer-transaction"]["amount"] / 1000000) * -1.0
            else:
                data["amount"] = float(transaction["asset-transfer-transaction"]["amount"] / 1000000)
            data["tx"] = str(transaction["id"])
            data["sensor"] = self.getDeviceID(transaction)
            data["timestamp"] = int(transaction["round-time"])
            data["current_price"] = float(data["amount"]) * self.CURRENT_VALUE_PLANET
            data["previous_price"] = self.getPriceFromDate(data["amount"], data["timestamp"])
            if(transaction['sender'] == self.wallet):
                data["price_difference"] = self.getPriceDifference(data["current_price"], data["previous_price"]) * -1.0
            else:
                data["price_difference"] = self.getPriceDifference(data["current_price"], data["previous_price"])

            if(self.cli_args['get'] == 'devices'):
                data['device'] = self.getDeviceID(transaction)
            
            self.DATA_TRANSACTIONS.append(data)

            #Update Stuff
            self.CURRENT_BALANCE_VALUE += float(data["current_price"])
            if(data["previous_price"] == None):
                self.PREVIOUS_BALANCE_VALUE += 0
            else:
                self.PREVIOUS_BALANCE_VALUE += float(data["previous_price"])

            index += 1
            if(self.cli_args['verbose']):
                print(f"Progress - {index}/{len(transactions)} Transactions")
            sleep(0.1)
        
        self.BALANCE_DIFFERENCE = self.CURRENT_BALANCE_VALUE - self.PREVIOUS_BALANCE_VALUE


    def getCurrentPrice(self, amount):
        value = self.cg.get_price(ids='planetwatch', vs_currencies=self.currency)["planetwatch"][self.currency]
        return amount * value

    def getPriceFromDate(self, amount, date):
        while(True):
            try:
                json_body = self.cg.get_coin_market_chart_range_by_id(id="planetwatch", vs_currency=self.currency, from_timestamp=(date - 1500), to_timestamp=(date + 3600))
                break
            except:
                print("Hit Ratelimit. Waiting 15s To Fetch Data Again!")
                sleep(15)
                continue
        if(len(json_body["prices"]) == 0):
            return None
        for x in json_body["prices"]:
            time_unix = x[0]
            if(time_unix >= (date * 1000)):
                value = x[1]
                return amount * value
        return None

    def getPriceDifference(self, price_now, previous_price):
        if(previous_price == None):
            previous_price = 0.0
        if(price_now == None):
            price_now = 0.0
        return price_now - previous_price

    def getDeviceID(self, transaction):
        if('note' in transaction):
            base_64_note = transaction['note']
            note_data = (base64.b64decode((base_64_note).encode('utf-8'))).decode('utf-8')
            note_data = json.loads(note_data)
            return note_data['deviceId']
        else:
            return None


    def createDataTableJson(self):
        self.DATA_TRANSACTIONS = {
            "Wallet": self.wallet,
            "Balance_Tokens": self.CURRENT_BALANCE,
            "Per_Token_Fiat": self.CURRENT_VALUE_PLANET,
            "Current_Value_Fiat": self.CURRENT_BALANCE_VALUE,
            "Previous_Value_Fiat": self.PREVIOUS_BALANCE_VALUE,
            "Difference_Fiat": self.BALANCE_DIFFERENCE,
            "Data": self.DATA_TRANSACTIONS
        }

    def createTable(self):
        table = [[
            "Nr",
            "Amount",
            "Sensor"
            "Date",
            f"Initial Value {self.CURRENCY_SYMBOL}",
            f"Current Value {self.CURRENCY_SYMBOL}",
            f"Difference {self.CURRENCY_SYMBOL}"]]
        index = 1
        for transaction in self.DATA_TRANSACTIONS['Data']:
            table_data_entry = []
            table_data_entry.append(index)
            table_data_entry.append(str(transaction["amount"]))
            table_data_entry.append(str(transaction["sensor"]))
            utc_time = datetime.utcfromtimestamp(int(transaction["timestamp"]))
            if(transaction["previous_price"] == None):
                utc_time = utc_time.strftime("%Y-%m-%d %H:%M:%S (UTC)")
            else:
                utc_time = utc_time.strftime("%Y-%m-%d (UTC)")
            table_data_entry.append(str(utc_time))
            table_data_entry.append(str(transaction["previous_price"]))
            table_data_entry.append(str(transaction["current_price"]))
            table_data_entry.append(str(transaction["price_difference"]))
            table.append(table_data_entry)
            index += 1
        return table

    def printWalletTransactions(self):
        print(f"++++++++++ Wallet: {self.wallet}")
        print(f"Current PlanetWatch Token Price: {self.CURRENT_VALUE_PLANET} {self.CURRENCY_SYMBOL}")
        print("Statistics:")
        print(f"    Current Balance: {self.CURRENT_BALANCE} Tokens")
        print(f"    Current Value: {self.CURRENT_BALANCE_VALUE} {self.CURRENCY_SYMBOL}")
        print(f"    Previous Value: {self.PREVIOUS_BALANCE_VALUE} {self.CURRENCY_SYMBOL}")
        print(f"    Difference: {str(self.BALANCE_DIFFERENCE)} {self.CURRENCY_SYMBOL}")
        print("")

        
        print(tabulate.tabulate(self.DATA_TABLE, headers='firstrow', numalign="right"))



    def saveToCSV(self):
        header = self.DATA_TABLE[0]
        content = self.DATA_TABLE
        content.pop(0)
        PATH = self.cli_args['csv']
        with open(f'{PATH}/{self.wallet}.csv', 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(content)
            f.close()

    def exportData(self):
        if(self.cli_args['export'] != None):
            PATH = self.cli_args['export']
            if(self.cli_args['format'] == 'json'):
                with open(f'{PATH}/{self.wallet}.json', 'w') as f:
                    json.dump(self.DATA_TRANSACTIONS, f)
                    f.close()
            else:
                with open(f'{PATH}/{self.wallet}.txt', 'w') as f:
                    f.write(tabulate.tabulate(self.DATA_TABLE, headers='firstrow', numalign="right"))
                    f.close()

        if(self.cli_args['csv'] != None):
            self.saveToCSV()