import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

class MorphoAPIClient:
    """Python client for accessing Morpho market data via GraphQL API"""
    
    def __init__(self):
        self.base_url = "https://api.morpho.org/graphql"
    
    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute a GraphQL query against the Morpho API"""
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(self.base_url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")
        
        return result["data"]
    
    def get_market_by_id(self, unique_key: str, chain_id: int = 1) -> Dict:
        """
        Get detailed information for a specific market by its unique key
        
        Args:
            unique_key: The market's unique identifier
            chain_id: Chain ID (1 for Ethereum, 8453 for Base)
        
        Returns:
            Dictionary containing market data including supply, borrow, liquidity
        """
        query = """
        query GetMarketById($uniqueKey: String!, $chainId: Int!) {
            marketByUniqueKey(uniqueKey: $uniqueKey, chainId: $chainId) {
                uniqueKey
                lltv
                oracleAddress
                irmAddress
                loanAsset {
                    address
                    symbol
                    decimals
                }
                collateralAsset {
                    address
                    symbol
                    decimals
                }
                state {
                    collateralAssets
                    collateralAssetsUsd
                    borrowAssets
                    borrowAssetsUsd
                    supplyAssets
                    supplyAssetsUsd
                    liquidityAssets
                    liquidityAssetsUsd
                    supplyApy
                    borrowApy
                    fee
                    utilization
                    rewards {
                        asset { address, symbol }
                        supplyApr
                        borrowApr
                    }
                }
                warnings {
                    type
                    level
                }
            }
        }
        """
        
        variables = {
            "uniqueKey": unique_key,
            "chainId": chain_id
        }
        
        return self._execute_query(query, variables)

def get_stakehouse_situation():
    """Get detailed information for all the stakehouse markets"""
    client = MorphoAPIClient()
    
    # Stakehouse USDC positions on Morpho
    stakehouse_markets = [
        {
            "name": "cbBTC/USDC",
            "market_id": "0x64d65c9a2d91c36d56fbc42d69e979335320169b3df63bf92789e2c8883fcc64"
        },
        {
            "name": "WBTC/USDC",
            "market_id": "0x3a85e619751152991742810df6ec69ce473daef99e28a64ab2340d7b7ccfee49"
        },
        {
            "name": "wstETH/USDC",
            "market_id": "0xb323495f7e4148be5643a4ea4a8221eef163e4bccfdedc2a6f4696baacbc86cc"
        }
    ]
    
    print("\n=== Stakehouse USDC Vault Positions on Morpho ===")
    for market in stakehouse_markets:
        try:
            market_data = client.get_market_by_id(market["market_id"], chain_id=1)
            m = market_data["marketByUniqueKey"]
            
            if m:
                print(f"\nMarket: {market['name']}")
                print(f"Collateral: {m['collateralAsset']['symbol']}")
                print(f"Loan Asset: {m['loanAsset']['symbol']}")
                print(f"Total Supply: {float(m['state']['supplyAssetsUsd']):,.2f} {m['loanAsset']['symbol']} (${float(m['state']['supplyAssetsUsd']):,.2f})")
                print(f"Total Borrow: {float(m['state']['borrowAssetsUsd']):,.2f} {m['loanAsset']['symbol']} (${float(m['state']['borrowAssetsUsd']):,.2f})")
                print(f"Available Liquidity: {float(m['state']['liquidityAssetsUsd']):,.2f} {m['loanAsset']['symbol']} (${float(m['state']['liquidityAssetsUsd']):,.2f})")
                print(f"Supply APY: {float(m['state']['supplyApy']) * 100:.2f}%")
                print(f"Borrow APY: {float(m['state']['borrowApy']) * 100:.2f}%")
                print(f"Utilization: {float(m['state']['utilization']) * 100:.2f}%")
                
                if m['state'].get('rewards'):
                    print("Rewards:")
                    for reward in m['state']['rewards']:
                        print(f"  {reward['asset']['symbol']}: Supply APR {float(reward['supplyApr']) * 100:.2f}%")
            else:
                print(f"\nMarket {market['name']} not found")
        
        except Exception as e:
            print(f"\nError fetching {market['name']} market data: {e}")

if __name__ == "__main__":
    get_stakehouse_situation()