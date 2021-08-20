from typing import Union

try:
    from config import get_configuration, save_to_config
    from wallet.validators import ValidationError
    from wallet.btc import BlkHubApi, BtcValidator
    from wallet.eth import EthValidator, Web3Api
    from wallet.eos import EosioValidator
except ImportError:
    from ...config import get_configuration, save_to_config
    from ...wallet.validators import ValidationError
    from ...wallet.btc import BlkHubApi, BtcValidator
    from ...wallet.eth import EthValidator, Web3Api
    from ...wallet.eos import EosioValidator


def add_config_sub_parser(sub_parser, crypto_currency: str) -> None:
    """
    Add config subparser

    :param sub_parser: Parser object to be added to
    :param crypto_currency: Name of the cryptocurrency
    :return: None
    """
    parser = sub_parser.add_parser("config",
                                   help=f"View or edit {crypto_currency} "
                                        "configuration")
    parser.add_argument("key", nargs="?", type=str, default=None,
                        help="Define key to use")
    parser.add_argument("value", nargs="?", type=str, default=None,
                        help="Define a new value for the given section "
                             "and key")


def create_config_method(card_serial: Union[int, str], key: Union[str, None],
                         value: Union[str, None],
                         currency_name: str)  -> int:
    """
    Create config method for specific cryptocurrency

    :param card_serial: Serial number of the card used
    :param key: Key of the configuration dictionary to be edited
    :param value: Value to be inserted into configuration or None
    :param currency_name: Name of the crypto for which to create
     configuration
    :return: None
    """
    if value is not None:
        return write_config(card_serial, currency_name, key, value)
    if key is not None:
        return print_key_config(
            card_serial, currency_name, key)

    return print_section_config(card_serial, currency_name)


def read_config(card_serial: Union[int, str], exclude=None) -> None:
    """
    Prints contents of config.

    :param Union[int, str] card_serial: Serial number of the card used
    :param Dict exclude: Exclude section from printing

    :return: None
    """
    exclude = exclude or ["hidden"]
    config = get_configuration(card_serial)

    for section in config:
        if section in exclude:
            continue
        print(f"\n[{section.upper()}]")
        for key, value in config[section].items():
            print(f"{key}: {value}" + find_endpoint(section, key, value, " - Read only"))


def print_section_config(card_serial: Union[int, str], section: str) -> int:
    """
    Prints contents of a section from configuration.

    :param card_serial: Serial number of the card used
    :param section: Section of the configuration file wanted printed
    :return: Execution status
    """
    config = get_configuration(card_serial)
    if section not in config:
        print("No such section")
        return 1

    print(f"[{section.upper()}]")

    for key, value in config[section].items():
        print(f"{key}: {value}" + find_endpoint(section, key, value, " - YOU CAN'T EDIT THIS"))

    return 0


def print_key_config(card_serial: Union[int, str],
                     section: str, key: str) -> int:
    """
    Prints key and value from section in config.

    :param card_serial: Serial number of the card used
    :param section: Section of the configuration file wanted printed
    :param key: Name of the parameter we want to change
    :return: Execution status
    """
    config = get_configuration(card_serial)
    try:
        old_key = key
        key = "network" if key == "endpoint" and section != "eosio" else key
        value = config[section][key]
        endpoint = find_endpoint(section, key, value, " - YOU CAN'T EDIT THIS")
        if old_key == "endpoint" and section != "eosio":
            print(endpoint)
        else:
            print(f"{key}: {value}")

    except LookupError:
        print("No such section or key")
        return 1

    return 0


def find_endpoint(section: str, key: str, value: str, append: str = "") \
        -> str:
    if key == "network" and section in ["eth", "btc"]:
        if section == "eth":
            return f"\nendpoint: https://{Web3Api(None, value).get_domain()}{append}"
        elif section == "btc":
            return f"\nendpoint: {BlkHubApi.get_api(value)}{append}"

    return ""


def write_config(card_serial: Union[int, str],
                 section: str, key: str, value: str) -> int:
    """
    Writes new value at chosen section and key.

    :param card_serial: Serial number of the card used
    :param section: Section of the config file to write to
    :param key: Name of the parameter we want to change
    :param value: Value we want to insert into the configuration file
    :return: Execution status
    """
    config = get_configuration(card_serial)
    try:
        instance = eval(f"{section.capitalize()}Validator")()
    except NameError:
        print("Invalid section")
        return 1
    try:
        getattr(instance, key)
        setattr(instance, key, value)
    except ValidationError as error:
        valid = instance.__class__.__dict__[key]
        print(f"Invalid value for the {key.replace('_', ' ')}")
        if valid:
            if valid.valid_values:
                print("Valid values are:")
                print(valid.valid_values)
            else:
                print(error)
        return 1
    except AttributeError:
        pass

    try:
        config[section][key] = str(getattr(instance, key))
    except AttributeError:
        try:
            config[section][key]
        except LookupError:
            print("Invalid key")
            return 1

    save_to_config(card_serial, config)
    print("\nConfiguration is written into the config file")

    return 0
