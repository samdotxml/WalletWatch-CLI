import click


@click.command()
@click.option('--get', type=click.Choice(['all','rewards','tx', 'devices'], case_sensitive=False), required=True)
@click.option('--wallet', required=True)
@click.option('--currency', required=True)
@click.option('--csv')
@click.option('--verbose', is_flag=True)
@click.option('--silent', is_flag=True)
def main(**args):
    args = locals()
    print(args)


if __name__ == "__main__":
    main()