from qiwipyapi import Wallet

from objects.globals import config

p2p_wallet = Wallet(config["qiwi_phone"], p2p_sec_key=config["qiwi_token"])