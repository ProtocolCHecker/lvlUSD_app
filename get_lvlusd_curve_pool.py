from web3 import Web3

# Connect to the Ethereum network using Infura
web3 = Web3(Web3.HTTPProvider('https://lb.drpc.org/ethereum/AtiZvaKOcUmKq-AbTta3bRZYYOcQGAwR8J6pThukG97E'))


# Check if connected
if not web3.is_connected():
    raise Exception("Failed to connect to the Ethereum network")

# Pool and Gauge contract addresses for lvlUSD/USDC
lvlusd_usdc_pool_address = Web3.to_checksum_address('0x1220868672d5b10f3e1cb9ab519e4d0b08545ea4')
lvlusd_usdc_gauge_address = Web3.to_checksum_address('0x60483b4792a17c980a275449caf848084231543c')

# Pool and Gauge contract addresses for lvlUSD/slvlUSD
lvlusd_slvlusd_pool_address = Web3.to_checksum_address('0xF244324FBB57f09F0606FF088bC894b051d632Eb')
lvlusd_slvlusd_gauge_address = Web3.to_checksum_address('0x124853CAC208d40dDD84CF120E500FA2BDCc5D75')

# ABIs for the Pool and Gauge contracts
lvlusd_usdc_pool_abi = [
    {
        "constant": True,
        "inputs": [],
        "name": "get_balances",
        "outputs": [{"name": "", "type": "uint256[]"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

lvlusd_slvlusd_pool_abi = [
    {
        "constant": True,
        "inputs": [{"name": "arg0", "type": "uint256"}],
        "name": "balances",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

gauge_abi = [
    {
        "constant": True,
        "inputs": [],
        "name": "reward_count",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "arg0", "type": "uint256"}],
        "name": "reward_tokens",
        "outputs": [{"name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_addr", "type": "address"}, {"name": "_token", "type": "address"}],
        "name": "claimed_reward",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

# Initialize contract instances for lvlUSD/USDC
lvlusd_usdc_pool_contract = web3.eth.contract(address=lvlusd_usdc_pool_address, abi=lvlusd_usdc_pool_abi)

# Initialize contract instances for lvlUSD/slvlUSD
lvlusd_slvlusd_pool_contract = web3.eth.contract(address=lvlusd_slvlusd_pool_address, abi=lvlusd_slvlusd_pool_abi)

def get_token_balances(pool_contract, pool_name, abi_type='get_balances'):
    try:
        if abi_type == 'get_balances':
            # For lvlUSD/USDC pool
            balances = pool_contract.functions.get_balances().call()
            lvlUSD_balance = balances[0] / (10 ** 6)
            other_token_balance = balances[1] / (10 ** 18)
        else:
            # For lvlUSD/slvlUSD pool
            balances = [pool_contract.functions.balances(i).call() for i in range(2)]
            lvlUSD_balance = balances[0] / (10 ** 18)
            other_token_balance = balances[1] / (10 ** 18)

        print(f'{pool_name} Token Balances:', balances)

        print(f'{pool_name} lvlUSD Balance:', lvlUSD_balance)
        if pool_name == 'lvlUSD/USDC Pool':
            print(f'{pool_name} USDC Balance:', other_token_balance)
        else:
            print(f'{pool_name} slvlUSD Balance:', other_token_balance)
    except Exception as e:
        print(f'Error for {pool_name}:', e)

# Get token balances for both pools
get_token_balances(lvlusd_usdc_pool_contract, 'lvlUSD/USDC Pool', 'get_balances')
get_token_balances(lvlusd_slvlusd_pool_contract, 'lvlUSD/slvlUSD Pool', 'balances')
