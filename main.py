import click
import sys
import core


@click.command()
@click.option('--get', type=click.Choice(['all','rewards','tx','devices'], case_sensitive=False), required=True)
@click.option('--wallet', required=True)
@click.option('--currency', required=True)
@click.option('--format', type=click.Choice(['json','table'], case_sensitive=False), default='table')
@click.option('--export')
@click.option('--csv')
@click.option('--verbose', is_flag=True)
@click.option('--silent', is_flag=True)
@click.option('--round', is_flag=True)
def main(**args):
    args = locals()
    checkWalletLength(args['args']['wallet'])
    checkConflicts(args)
    checkCurrency(args['args']['currency'])
    object = core.Wallet_Info(args['args']['wallet'], args['args']['currency'], args)
    


def checkWalletLength(wallet):
    if(len(wallet) != 58):
        print(len(wallet))
        print("This Wallet's Length Is Not 52 Characters. Enter A Real Wallet")
        sys.exit()

def checkConflicts(args):
    if(args['args']['silent'] and args['args']['verbose']):
        print('Conflict Found. You Can Not Run --silent & --verbose Flags At The Same Time')
        sys.exit()

def checkCurrency(symbol):
    currencies = core.requests.get('https://api.coingecko.com/api/v3/simple/supported_vs_currencies').json()
    symbol = str(symbol).lower()
    for currency in currencies:
        if(currency == symbol):
            return True
    print('Currency Entered Not Found. Checkout https://api.coingecko.com/api/v3/simple/supported_vs_currencies To Make Sure You Chose Correctly')
    sys.exit()



if __name__ == "__main__":
    main()