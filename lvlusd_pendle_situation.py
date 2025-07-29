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

def get_lvlusd_pendle_situation():
    """Get detailed information for all the lvlUSD Pendle markets"""
    client = MorphoAPIClient()
    
    # lvlUSD positions on Pendle through Morpho
    lvlusd_markets = [
        {
            "name": "PT-lvlUSD-25SEP2025/lvlUSD",
            "market_id": "0xa4bb66e932dfa4b54c0b612dfffdbdc426f7906306a78178acd8562739121b9a"
        },
        {
            "name": "PT-lvlUSD-25SEP2025/USDC",
            "market_id": "0xe61a903174169e4897669e9bc4419eb7582b36d1a3d3df633dccab88da6e2ccd"
        }
    ]
    
    print("\n=== lvlUSD Positions on Pendle through Morpho ===")
    for market in lvlusd_markets:
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
    get_lvlusd_pendle_situation()