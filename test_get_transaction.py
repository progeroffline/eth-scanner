import httpx
from environs import Env
from rich import print
from web3 import HTTPProvider, Web3
from web3.exceptions import Web3ValueError

env = Env()
env.read_env()


INFURA_PUBLIC_API_KEY = env.str("INFURA_PUBLIC_API_KEY")
ETHERSCAN_API_KEY = env.str("ETHERSCAN_API_KEY")
infura_url = f"https://mainnet.infura.io/v3/{INFURA_PUBLIC_API_KEY}"
infura_wss = f"wss://mainnet.infura.io/ws/v3/{INFURA_PUBLIC_API_KEY}"
w3 = Web3(HTTPProvider(infura_url))


def get_contract_abi(contract_address: str) -> str:
    response = httpx.Client().get(
        "https://api.etherscan.io/api",
        params={
            "module": "contract",
            "action": "getabi",
            "address": contract_address,
            "apikey": ETHERSCAN_API_KEY,
        },
    )
    if response.status_code == 200:
        return response.json()["result"]
    return ""


def get_trasaction_id(transaction_id: str) -> None:
    transaction = w3.eth.get_transaction(transaction_id)
    transaction_contract = w3.eth.wait_for_transaction_receipt(transaction_id)
    print(transaction)
    contract_address: str | None = None

    for log in transaction_contract["logs"]:
        if address := log.get("address"):
            contract_address = address
            break

    if contract_address:
        contract_abi = get_contract_abi(contract_address)
        transaction_contract = w3.eth.contract(
            address=contract_address,
            abi=contract_abi,
        )
        print(transaction_contract.address)


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2:
        transaction_id = sys.argv[1]
        get_trasaction_id(transaction_id)
