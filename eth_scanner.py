import asyncio

import httpx
from environs import Env
from rich import print
from web3 import AsyncHTTPProvider, AsyncWeb3
from web3.exceptions import TransactionNotFound, Web3ValueError

env = Env()
env.read_env()


INFURA_PUBLIC_API_KEY = env.str("INFURA_PUBLIC_API_KEY")
ETHERSCAN_API_KEY = env.str("ETHERSCAN_API_KEY")
infura_url = f"https://mainnet.infura.io/v3/{INFURA_PUBLIC_API_KEY}"
infura_wss = f"wss://mainnet.infura.io/ws/v3/{INFURA_PUBLIC_API_KEY}"
w3 = AsyncWeb3(AsyncHTTPProvider(infura_url))


async def get_contract_abi(contract_address: str) -> str:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
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
    except httpx.ReadTimeout:
        return await get_contract_abi(contract_address)


async def scan_last_blocks():
    last_blocks = await w3.eth.get_block("latest")
    if last_blocks.get("transactions") is None:
        return

    for transaction in last_blocks["transactions"]:
        transaction_id = "0x" + transaction.hex()
        try:
            transaction = await w3.eth.get_transaction(transaction_id)
        except TransactionNotFound:
            continue

        try:
            transaction_contract = await w3.eth.wait_for_transaction_receipt(
                transaction_id,
            )
        except TransactionNotFound:
            continue

        contract_address: str | None = transaction_contract["contractAddress"]
        function_name, args = None, None
        if contract_address:
            try:
                contract_abi = await get_contract_abi(contract_address)
                transaction_contract = w3.eth.contract(
                    address=contract_address,
                    abi=contract_abi,
                )
            except ValueError:
                continue

            function, args = None, None
            try:
                function, args = transaction_contract.decode_function_input(
                    transaction["input"],
                )
                function_name = function.fn_name
            except Web3ValueError:
                function_name = function

            print("---------------------------------------------")
            print(f"Transaction id: {transaction_id}")
            print(f"Contract address: {contract_address}")
            print(f"Contract: {function_name=} {args=}")


if __name__ == "__main__":
    asyncio.run(scan_last_blocks())
