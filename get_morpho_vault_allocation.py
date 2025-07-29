import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

class MorphoAPIClient:
    """
    Python client for accessing Morpho market data via GraphQL API
    API Endpoint: https://api.morpho.org/graphql
    """
    
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
    
    def get_all_markets(self, whitelisted_only: bool = False, chain_ids: List[int] = [1]) -> Dict:
        """
        Get list of all markets or whitelisted markets only
        
        Args:
            whitelisted_only: If True, returns only whitelisted markets
            chain_ids: List of chain IDs to query
        
        Returns:
            Dictionary containing list of markets
        """
        where_clause = ""
        if whitelisted_only:
            where_clause = "where: { whitelisted: true, chainId_in: $chainIds }"
        else:
            where_clause = "where: { chainId_in: $chainIds }"
        
        query = f"""
        query GetAllMarkets($chainIds: [Int!]!) {{
            markets(
                first: 100
                orderBy: SupplyAssetsUsd
                orderDirection: Desc
                {where_clause}
            ) {{
                items {{
                    uniqueKey
                    whitelisted
                    lltv
                    oracleAddress
                    irmAddress
                    loanAsset {{
                        address
                        symbol
                        decimals
                    }}
                    collateralAsset {{
                        address
                        symbol
                        decimals
                    }}
                    state {{
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
                    }}
                }}
            }}
        }}
        """
        
        variables = {"chainIds": chain_ids}
        return self._execute_query(query, variables)
    
    def get_market_positions(self, market_unique_key: str, limit: int = 10) -> Dict:
        """
        Get user positions for a specific market
        
        Args:
            market_unique_key: The market's unique identifier
            limit: Number of positions to return
        
        Returns:
            Dictionary containing user positions
        """
        query = """
        query GetMarketPositions($marketUniqueKey: String!, $limit: Int!) {
            marketPositions(
                first: $limit
                orderBy: BorrowAssetsUsd
                orderDirection: Desc
                where: {
                    marketUniqueKey_in: [$marketUniqueKey]
                }
            ) {
                items {
                    user { address }
                    market {
                        uniqueKey
                        loanAsset { symbol }
                        collateralAsset { symbol }
                    }
                    state {
                        supplyShares
                        supplyAssets
                        supplyAssetsUsd
                        borrowShares
                        borrowAssets
                        borrowAssetsUsd
                        collateral
                        collateralUsd
                    }
                }
            }
        }
        """
        
        variables = {
            "marketUniqueKey": market_unique_key,
            "limit": limit
        }
        
        return self._execute_query(query, variables)
    
    def get_historical_data(self, unique_key: str, start_timestamp: int, 
                          end_timestamp: int, interval: str = "HOUR", 
                          chain_id: int = 1) -> Dict:
        """
        Get historical APY and market state data
        
        Args:
            unique_key: The market's unique identifier
            start_timestamp: Start time in UNIX timestamp
            end_timestamp: End time in UNIX timestamp
            interval: Time interval (YEAR, QUARTER, MONTH, WEEK, DAY, HOUR, etc.)
            chain_id: Chain ID
        
        Returns:
            Dictionary containing historical data
        """
        query = """
        query GetHistoricalData($uniqueKey: String!, $chainId: Int!, $options: TimeseriesOptions!) {
            marketByUniqueKey(uniqueKey: $uniqueKey, chainId: $chainId) {
                uniqueKey
                historicalState {
                    supplyApy(options: $options) {
                        x
                        y
                    }
                    borrowApy(options: $options) {
                        x
                        y
                    }
                    supplyAssetsUsd(options: $options) {
                        x
                        y
                    }
                    borrowAssetsUsd(options: $options) {
                        x
                        y
                    }
                }
            }
        }
        """
        
        variables = {
            "uniqueKey": unique_key,
            "chainId": chain_id,
            "options": {
                "startTimestamp": start_timestamp,
                "endTimestamp": end_timestamp,
                "interval": interval
            }
        }
        
        return self._execute_query(query, variables)
    
    def get_asset_price(self, asset_symbols: List[str], chain_ids: List[int] = [1]) -> Dict:
        """
        Get current USD price for specific assets
        
        Args:
            asset_symbols: List of asset symbols (e.g., ["WETH", "USDC"])
            chain_ids: List of chain IDs to query
        
        Returns:
            Dictionary containing asset prices
        """
        query = """
        query GetAssetsWithPrice($symbols: [String!]!, $chainIds: [Int!]!) {
            assets(where: { symbol_in: $symbols, chainId_in: $chainIds }) {
                items {
                    symbol
                    address
                    priceUsd
                    chain {
                        id
                        network
                    }
                }
            }
        }
        """
        
        variables = {
            "symbols": asset_symbols,
            "chainIds": chain_ids
        }
        
        return self._execute_query(query, variables)
    
    def get_vault_allocation(self, vault_address: str, chain_id: int = 1) -> Dict:
        """
        Get vault allocation distribution across Morpho markets
        
        Args:
            vault_address: The vault's contract address
            chain_id: Chain ID (1 for Ethereum, 8453 for Base)
        
        Returns:
            Dictionary containing vault allocation data across markets
        """
        query = """
        query GetVaultAllocation($vaultAddress: String!, $chainId: Int!) {
            vaultByAddress(address: $vaultAddress, chainId: $chainId) {
                address
                symbol
                name
                asset {
                    address
                    symbol
                    decimals
                }
                state {
                    apy
                    netApy
                    totalAssets
                    totalAssetsUsd
                    fee
                    timelock
                    rewards {
                        asset { 
                            address
                            symbol 
                        }
                        supplyApr
                        yearlySupplyTokens
                    }
                    allocation {
                        supplyCap
                        supplyAssets
                        supplyAssetsUsd
                        enabled
                        market {
                            uniqueKey
                            lltv
                            oracleAddress
                            irmAddress
                            loanAsset {
                                address
                                symbol
                                name
                                decimals
                            }
                            collateralAsset {
                                address
                                symbol
                                name
                                decimals
                            }
                            state {
                                supplyApy
                                borrowApy
                                utilization
                                supplyAssets
                                supplyAssetsUsd
                                borrowAssets
                                borrowAssetsUsd
                                liquidityAssets
                                liquidityAssetsUsd
                                rewards {
                                    asset { address, symbol }
                                    supplyApr
                                    borrowApr
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "vaultAddress": vault_address,
            "chainId": chain_id
        }
        
        return self._execute_query(query, variables)
    
    def get_all_vaults(self, limit: int = 100, chain_ids: List[int] = [1]) -> Dict:
        """
        Get list of all vaults ordered by total assets
        
        Args:
            limit: Number of vaults to return
            chain_ids: List of chain IDs to query
        
        Returns:
            Dictionary containing list of vaults
        """
        query = """
        query GetAllVaults($limit: Int!, $chainIds: [Int!]!) {
            vaults(
                first: $limit
                orderBy: TotalAssetsUsd
                orderDirection: Desc
                where: { chainId_in: $chainIds }
            ) {
                items {
                    address
                    symbol
                    name
                    whitelisted
                    asset {
                        address
                        symbol
                        decimals
                    }
                    state {
                        apy
                        netApy
                        totalAssets
                        totalAssetsUsd
                        fee
                        timelock
                    }
                }
            }
        }
        """
        
        variables = {
            "limit": limit,
            "chainIds": chain_ids
        }
        
        return self._execute_query(query, variables)


def get_specific_markets_info():
    """Get detailed information for all the specified markets"""
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
    
    # slvlUSD positions on Pendle through Morpho
    slvlusd_markets = [
        {
            "name": "PT-slvlUSD-25SEP2025/lvlUSD",
            "market_id": "0x8ebcaf72c7cd75e8c621ec77ec343b3152c48908c4a6e217da82fe6af23c1928"
        },
        {
            "name": "PT-slvlUSD-25SEP2025/USDC",
            "market_id": "0x4005ba6eb7d2221fe58102bd320aa6d83c47b212771bc950ab71c5074d9ab0ec"
        }
    ]
    
    print("\n=== Stakehouse USDC Positions on Morpho ===")
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
    
    print("\n=== lvlUSD Positions on Pendle through Morpho ===")
    for market in lvlusd_markets:
        try:
            market_data = client.get_market_by_id(market["market_id"], chain_id=1)
            m = market_data["marketByUniqueKey"]
            
            if m:
                print(f"\nMarket: {market['name']}")
                print(f"Collateral: {m['collateralAsset']['symbol']}")
                print(f"Loan Asset: {m['loanAsset']['symbol']}")
                print(f"Total Supply: {float(m['state']['supplyAssets']):,.2f} {m['loanAsset']['symbol']} (${float(m['state']['supplyAssetsUsd']):,.2f})")
                print(f"Total Borrow: {float(m['state']['borrowAssets']):,.2f} {m['loanAsset']['symbol']} (${float(m['state']['borrowAssetsUsd']):,.2f})")
                print(f"Available Liquidity: {float(m['state']['liquidityAssets']):,.2f} {m['loanAsset']['symbol']} (${float(m['state']['liquidityAssetsUsd']):,.2f})")
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
    
    print("\n=== slvlUSD Positions on Pendle through Morpho ===")
    for market in slvlusd_markets:
        try:
            market_data = client.get_market_by_id(market["market_id"], chain_id=1)
            m = market_data["marketByUniqueKey"]
            
            if m:
                print(f"\nMarket: {market['name']}")
                print(f"Collateral: {m['collateralAsset']['symbol']}")
                print(f"Loan Asset: {m['loanAsset']['symbol']}")
                print(f"Total Supply: {float(m['state']['supplyAssets']):,.2f} {m['loanAsset']['symbol']} (${float(m['state']['supplyAssetsUsd']):,.2f})")
                print(f"Total Borrow: {float(m['state']['borrowAssets']):,.2f} {m['loanAsset']['symbol']} (${float(m['state']['borrowAssetsUsd']):,.2f})")
                print(f"Available Liquidity: {float(m['state']['liquidityAssets']):,.2f} {m['loanAsset']['symbol']} (${float(m['state']['liquidityAssetsUsd']):,.2f})")
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

def main():
    """Example usage of the Morpho API client"""
    client = MorphoAPIClient()
    
    # Original example usage
    cbbtc_usdc_market_id = "0x64d65c9a2d91c36d56fbc42d69e979335320169b3df63bf92789e2c8883fcc64"
    
    print("=== Getting cbBTC/USDC Market Data ===")
    try:
        market_data = client.get_market_by_id(cbbtc_usdc_market_id, chain_id=1)
        market = market_data["marketByUniqueKey"]
        
        if market:
            print(f"Market: {market['collateralAsset']['symbol']}/{market['loanAsset']['symbol']}")
            print(f"Total Supply: {market['state']['supplyAssets']} {market['loanAsset']['symbol']}")
            print(f"Total Borrow: {market['state']['borrowAssets']} {market['loanAsset']['symbol']}")
            print(f"Available Liquidity: {market['state']['liquidityAssets']} {market['loanAsset']['symbol']}")
            print(f"Supply APY: {float(market['state']['supplyApy']) * 100:.2f}%")
            print(f"Borrow APY: {float(market['state']['borrowApy']) * 100:.2f}%")
            print(f"Utilization: {float(market['state']['utilization']) * 100:.2f}%")
            print(f"Total Supply USD: ${float(market['state']['supplyAssetsUsd']):,.2f}")
            print(f"Total Borrow USD: ${float(market['state']['borrowAssetsUsd']):,.2f}")
            print(f"Available Liquidity USD: ${float(market['state']['liquidityAssetsUsd']):,.2f}")
        else:
            print("Market not found")
    
    except Exception as e:
        print(f"Error fetching market data: {e}")
    
    # Get information for all specified markets
    get_specific_markets_info()


def get_vault_allocation_summary(client: MorphoAPIClient, vault_address: str, chain_id: int = 1) -> Dict:
    """
    Helper function to get a clean summary of vault allocation across markets
    
    Args:
        client: MorphoAPIClient instance
        vault_address: The vault's contract address
        chain_id: Chain ID
    
    Returns:
        Dictionary with clean vault allocation summary
    """
    data = client.get_vault_allocation(vault_address, chain_id)
    vault = data["vaultByAddress"]
    
    if not vault:
        return {}
    
    # Process allocations
    allocations = []
    total_assets_usd = float(vault['state']['totalAssetsUsd'])
    
    for allocation in vault['state']['allocation']:
        if float(allocation['supplyAssets']) > 0:  # Only include markets with actual allocation
            market = allocation['market']
            supply_usd = float(allocation['supplyAssetsUsd'])
            
            allocation_info = {
                "market_id": market['uniqueKey'],
                "market_pair": f"{market['collateralAsset']['symbol']}/{market['loanAsset']['symbol']}",
                "supply_assets": float(allocation['supplyAssets']),
                "supply_assets_usd": supply_usd,
                "allocation_percentage": (supply_usd / total_assets_usd) * 100,
                "supply_cap": float(allocation['supplyCap']),
                "enabled": allocation['enabled'],
                "market_apy": float(market['state']['supplyApy']) * 100,
                "market_utilization": float(market['state']['utilization']) * 100,
                "loan_asset": market['loanAsset']['symbol'],
                "collateral_asset": market['collateralAsset']['symbol']
            }
            allocations.append(allocation_info)
    
    # Sort by allocation percentage (highest first)
    allocations.sort(key=lambda x: x['allocation_percentage'], reverse=True)
    
    return {
        "vault_address": vault['address'],
        "vault_name": vault['name'],
        "vault_symbol": vault['symbol'],
        "underlying_asset": vault['asset']['symbol'],
        "total_assets": float(vault['state']['totalAssets']),
        "total_assets_usd": total_assets_usd,
        "vault_apy": float(vault['state']['apy']) * 100,
        "net_apy": float(vault['state']['netApy']) * 100,
        "fee": float(vault['state']['fee']) * 100,
        "allocations": allocations,
        "total_allocated_usd": sum(a['supply_assets_usd'] for a in allocations),
        "utilization_percentage": (sum(a['supply_assets_usd'] for a in allocations) / total_assets_usd) * 100
    }

def analyze_vault_diversification(vault_summary: Dict) -> Dict:
    """
    Analyze vault diversification metrics
    
    Args:
        vault_summary: Output from get_vault_allocation_summary()
    
    Returns:
        Dictionary with diversification analysis
    """
    allocations = vault_summary['allocations']
    
    if not allocations:
        return {}
    
    # Calculate diversification metrics
    num_markets = len(allocations)
    largest_allocation = max(a['allocation_percentage'] for a in allocations)
    top_3_allocation = sum(sorted([a['allocation_percentage'] for a in allocations], reverse=True)[:3])
    
    # Calculate Herfindahl-Hirschman Index (HHI) for concentration
    hhi = sum((a['allocation_percentage'] / 100) ** 2 for a in allocations)
    
    # Get unique collateral types
    collateral_types = set(a['collateral_asset'] for a in allocations)
    
    return {
        "num_markets": num_markets,
        "num_collateral_types": len(collateral_types),
        "largest_allocation_pct": largest_allocation,
        "top_3_allocation_pct": top_3_allocation,
        "herfindahl_index": hhi,  # Lower = more diversified (0-1 scale)
        "diversification_score": 1 - hhi,  # Higher = more diversified
        "collateral_types": list(collateral_types)
    }

if __name__ == "__main__":
    main()