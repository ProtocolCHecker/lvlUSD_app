from web3 import Web3

# Initialize Web3 connection using your drpc node
web3 = Web3(Web3.HTTPProvider('https://lb.drpc.org/ethereum/AtiZvaKOcUmKq-AbTta3bRZYYOcQGAwR8J6pThukG97E'))

# Contract addresses
aEthUSDC_contract_address = '0x98C23E9d8f34FEFb1B7BD6a91B7FF122F4e16F5c'
variableDebtEthUSDC_contract_address = '0x72E95b8931767C79bA4EeE721354d6E99a61D004'

# Simplified ABIs
aEthUSDC_abi = [
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

variableDebtEthUSDC_abi = [
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

# Initialize contract instances
aEthUSDC_contract = web3.eth.contract(address=aEthUSDC_contract_address, abi=aEthUSDC_abi)
variableDebtEthUSDC_contract = web3.eth.contract(address=variableDebtEthUSDC_contract_address, abi=variableDebtEthUSDC_abi)

# Fetch total supply and total borrow
total_supply = aEthUSDC_contract.functions.totalSupply().call() / 10**6
total_borrow = variableDebtEthUSDC_contract.functions.totalSupply().call() /10**6

# Calculate available liquidity
available_liquidity = total_supply - total_borrow

print(f"Total Supply USD: ${total_supply}")
print(f"Total Borrow USD: ${total_borrow}")
print(f"Available Liquidity: ${available_liquidity}")
