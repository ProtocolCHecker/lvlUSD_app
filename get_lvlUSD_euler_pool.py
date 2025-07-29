import requests
from decimal import Decimal

# Vault address
vault_address = "0xF2ec2d8fE1351bAFF31643855C0f4D1E63Bd1ce4"

# API URL
url = f"https://app.euler.finance/api/v1/vault?chainId=1&vaults={vault_address}&type=classic"

def parse_bigint(value):
    """Converts Euler's __bigint__ strings to Decimal"""
    if isinstance(value, str) and value.startswith("__bigint__"):
        return Decimal(value.replace("__bigint__", ""))
    return Decimal(value)

def fetch_vault_data():
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    vault_data = data.get(vault_address, {})

    # Extract values
    total_borrowed = parse_bigint(vault_data.get("totalBorrowed", "0"))
    total_cash = parse_bigint(vault_data.get("totalCash", "0"))
    total_supply = total_borrowed + total_cash
    available_liquidity = total_cash

    # Placeholder for APY
    apy = None  # Euler interest rate model is not populated here

    # Print results
    print("Vault:", vault_address)
    print(f"Total Borrowed       : {total_borrowed / 1e18:.6f}")
    print(f"Total Supplied       : {total_supply / 1e18:.6f}")
    print(f"Available Liquidity  : {available_liquidity / 1e18:.6f}")
    print(f"APY                  : {apy}")

if __name__ == "__main__":
    fetch_vault_data()
