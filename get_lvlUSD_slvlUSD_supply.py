from web3 import Web3

# Initialize Web3 connection
web3 = Web3(Web3.HTTPProvider('https://lb.drpc.org/ethereum/AtiZvaKOcUmKq-AbTta3bRZYYOcQGAwR8J6pThukG97E'))

# Contract addresses
lvlUSD_contract_address = "0x7C1156E515aA1A2E851674120074968C905aAF37"
slvlUSD_contract_address = "0x4737D9b4592B40d51e110b94c9C043c6654067Ae"

# Contract ABIs (only the necessary parts)
lvlUSD_abi = [
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

slvlUSD_abi = [
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
lvlUSD_contract = web3.eth.contract(address=lvlUSD_contract_address, abi=lvlUSD_abi) 
slvlUSD_contract = web3.eth.contract(address=slvlUSD_contract_address, abi=slvlUSD_abi) 

# Fetch total supply
lvlUSD_total_supply = lvlUSD_contract.functions.totalSupply().call() / 10**18
slvlUSD_total_supply = slvlUSD_contract.functions.totalSupply().call() / 10**18

# Calculate the percentage
percentage = (slvlUSD_total_supply / lvlUSD_total_supply) * 100

# Print the results
print(f"Total supply of lvlUSD: {lvlUSD_total_supply}")
print(f"Total supply of slvlUSD: {slvlUSD_total_supply}")
print(f"Percentage of slvlUSD over lvlUSD: {percentage:.2f}%")
