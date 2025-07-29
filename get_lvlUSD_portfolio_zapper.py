#!/usr/bin/env python3
"""
Zapper API Portfolio Fetcher
This script fetches wallet portfolio data using the Zapper GraphQL API.
It supports multiple wallets, different networks, and provides detailed token information.
"""

import requests
import json
import sys
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

# Configuration
API_KEY = 'd4039e1b-6ff5-4931-903e-9ea82316c187'  # Replace with your actual Zapper API key
API_URL = 'https://public.zapper.xyz/graphql'

# Available chain IDs
SUPPORTED_CHAIN_IDS = {
    'Ethereum': 1,
    'Polygon': 137,
    'BSC': 56,
    'Arbitrum': 42161,
    'Optimism': 10,
    'Avalanche': 43114,
    'Fantom': 250,
    'Base': 8453,
    'ZKsync': 324
}

@dataclass
class DeFiPosition:
    """Data class to represent a DeFi position"""
    app_name: str
    app_slug: str
    network: str
    chain_id: int
    position_type: str
    balance_usd: float
    position_address: str = ""
    symbol: str = ""
    balance: float = 0.0
    underlying_tokens: List[dict] = None
    display_label: str = ""
    meta_type: str = ""

    def __post_init__(self):
        if self.underlying_tokens is None:
            self.underlying_tokens = []

    def __str__(self):
        base_info = f"{self.app_name} on {self.network}"
        if self.symbol:
            base_info += f" | {self.symbol}"
        if self.display_label:
            base_info += f" | {self.display_label}"
        if self.meta_type:
            base_info += f" | {self.meta_type}"
        base_info += f" | ${self.balance_usd:.2f}"
        return base_info

class ZapperAPI:
    """Zapper API client for fetching portfolio data"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'x-zapper-api-key': self.api_key
        })

    def fetch_defi_positions(self, addresses: List[str], chain_ids: List[int] = None) -> Dict[str, Any]:
        """Fetch DeFi positions (app balances) for given addresses and chain IDs"""
        if chain_ids is None:
            chain_ids = [1]  # Ethereum mainnet

        # Validate chain IDs
        valid_chain_ids = list(SUPPORTED_CHAIN_IDS.values())
        invalid_chains = [cid for cid in chain_ids if cid not in valid_chain_ids]
        if invalid_chains:
            print(f"Warning: Unsupported chain IDs will be ignored: {invalid_chains}")
            chain_ids = [cid for cid in chain_ids if cid in valid_chain_ids]

        # Query for DeFi positions (app balances)
        query = """
        query PortfolioV2($addresses: [Address!]!, $chainIds: [Int!]) {
            portfolioV2(addresses: $addresses, chainIds: $chainIds) {
                appBalances {
                    totalBalanceUSD
                    byApp(first: 50) {
                        edges {
                            node {
                                app {
                                    displayName
                                    slug
                                    description
                                    url
                                    category {
                                        name
                                    }
                                }
                                network {
                                    name
                                    chainId
                                }
                                balanceUSD
                                positionBalances(first: 20) {
                                    edges {
                                        node {
                                            ... on AppTokenPositionBalance {
                                                type
                                                address
                                                symbol
                                                balance
                                                balanceUSD
                                                price
                                                appId
                                                groupLabel
                                                tokens {
                                                    ... on BaseTokenPositionBalance {
                                                        type
                                                        address
                                                        network
                                                        balance
                                                        balanceUSD
                                                        symbol
                                                        decimals
                                                    }
                                                    ... on AppTokenPositionBalance {
                                                        type
                                                        address
                                                        network
                                                        balance
                                                        balanceUSD
                                                        symbol
                                                        decimals
                                                        tokens {
                                                            ... on BaseTokenPositionBalance {
                                                                type
                                                                address
                                                                network
                                                                balance
                                                                balanceUSD
                                                                symbol
                                                                decimals
                                                            }
                                                        }
                                                    }
                                                }
                                                displayProps {
                                                    label
                                                }
                                            }
                                            ... on ContractPositionBalance {
                                                type
                                                address
                                                balanceUSD
                                                tokens {
                                                    metaType
                                                    token {
                                                        ... on BaseTokenPositionBalance {
                                                            type
                                                            address
                                                            network
                                                            balance
                                                            balanceUSD
                                                            symbol
                                                            decimals
                                                        }
                                                        ... on AppTokenPositionBalance {
                                                            type
                                                            address
                                                            network
                                                            balance
                                                            balanceUSD
                                                            symbol
                                                            decimals
                                                        }
                                                    }
                                                }
                                                displayProps {
                                                    label
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        payload = {
            'query': query,
            'variables': {
                'addresses': addresses,
                'chainIds': chain_ids
            }
        }

        try:
            response = self.session.post(API_URL, json=payload, timeout=30)
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.reason}"
                if response.text:
                    try:
                        error_data = response.json()
                        if 'errors' in error_data:
                            error_msg += f"\nGraphQL Errors: {json.dumps(error_data['errors'], indent=2)}"
                        else:
                            error_msg += f"\nResponse: {response.text}"
                    except:
                        error_msg += f"\nResponse: {response.text}"
                raise Exception(error_msg)
            data = response.json()
            if 'errors' in data:
                raise Exception(f"GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
            return data['data']
        except requests.RequestException as e:
            raise Exception(f"Request failed: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {e}")

    def get_defi_positions(self, addresses: List[str], chain_ids: List[int] = None) -> List[DeFiPosition]:
        """Get DeFi positions as a list of DeFiPosition objects"""
        portfolio_data = self.fetch_defi_positions(addresses, chain_ids)
        defi_positions = []
        app_edges = portfolio_data['portfolioV2']['appBalances']['byApp']['edges']

        for app_edge in app_edges:
            app_node = app_edge['node']
            app_info = app_node['app']
            network_info = app_node['network']

            # Process each position within the app
            position_edges = app_node['positionBalances']['edges']
            for pos_edge in position_edges:
                pos_node = pos_edge['node']
                position_type = pos_node['type']

                if position_type == 'app-token':
                    position = DeFiPosition(
                        app_name=app_info['displayName'],
                        app_slug=app_info['slug'],
                        network=network_info['name'],
                        chain_id=network_info['chainId'],
                        position_type=position_type,
                        balance_usd=pos_node['balanceUSD'],
                        position_address=pos_node['address'],
                        symbol=pos_node.get('symbol', ''),
                        balance=pos_node.get('balance', 0.0),
                        display_label=pos_node.get('displayProps', {}).get('label', ''),
                        underlying_tokens=pos_node.get('tokens', [])
                    )
                    defi_positions.append(position)
                elif position_type == 'contract-position':
                    contract_tokens = pos_node.get('tokens', [])
                    if contract_tokens:
                        meta_types = {}
                        for token_info in contract_tokens:
                            meta_type = token_info.get('metaType', 'UNKNOWN')
                            if meta_type not in meta_types:
                                meta_types[meta_type] = []
                            meta_types[meta_type].append(token_info)

                        for meta_type, tokens in meta_types.items():
                            total_usd = sum(token['token'].get('balanceUSD', 0) for token in tokens)
                            position = DeFiPosition(
                                app_name=app_info['displayName'],
                                app_slug=app_info['slug'],
                                network=network_info['name'],
                                chain_id=network_info['chainId'],
                                position_type=position_type,
                                balance_usd=total_usd,
                                position_address=pos_node['address'],
                                display_label=pos_node.get('displayProps', {}).get('label', ''),
                                meta_type=meta_type,
                                underlying_tokens=tokens
                            )
                            defi_positions.append(position)
                    else:
                        position = DeFiPosition(
                            app_name=app_info['displayName'],
                            app_slug=app_info['slug'],
                            network=network_info['name'],
                            chain_id=network_info['chainId'],
                            position_type=position_type,
                            balance_usd=pos_node['balanceUSD'],
                            position_address=pos_node['address'],
                            display_label=pos_node.get('displayProps', {}).get('label', '')
                        )
                        defi_positions.append(position)
        return defi_positions

    def get_defi_summary(self, addresses: List[str], chain_ids: List[int] = None) -> Dict[str, Any]:
        """Get a summary of DeFi positions"""
        portfolio_data = self.fetch_defi_positions(addresses, chain_ids)
        defi_positions = self.get_defi_positions(addresses, chain_ids)

        total_value_usd = portfolio_data['portfolioV2']['appBalances']['totalBalanceUSD']
        position_count = len(defi_positions)

        chain_names = []
        if chain_ids:
            for cid in chain_ids:
                for name, id in SUPPORTED_CHAIN_IDS.items():
                    if id == cid:
                        chain_names.append(name)
                        break

        app_summary = {}
        for position in defi_positions:
            app_key = f"{position.app_name} ({position.network})"
            if app_key in app_summary:
                app_summary[app_key]['count'] += 1
                app_summary[app_key]['total_usd'] += position.balance_usd
            else:
                app_summary[app_key] = {
                    'app_name': position.app_name,
                    'network': position.network,
                    'count': 1,
                    'total_usd': position.balance_usd
                }

        meta_type_summary = {}
        for position in defi_positions:
            if position.meta_type:
                if position.meta_type in meta_type_summary:
                    meta_type_summary[position.meta_type]['count'] += 1
                    meta_type_summary[position.meta_type]['total_usd'] += position.balance_usd
                else:
                    meta_type_summary[position.meta_type] = {
                        'count': 1,
                        'total_usd': position.balance_usd
                    }

        return {
            'addresses': addresses,
            'chain_ids': chain_ids,
            'chain_names': chain_names,
            'total_value_usd': total_value_usd,
            'position_count': position_count,
            'unique_apps': len(app_summary),
            'app_summary': app_summary,
            'meta_type_summary': meta_type_summary,
            'timestamp': datetime.now().isoformat()
        }

def test_api_connection(api_key: str) -> bool:
    """Test if the API key and connection are working"""
    print("🔧 Testing API connection...")
    test_query = """
    query {
        __schema {
            types {
                name
            }
        }
    }
    """
    headers = {
        'Content-Type': 'application/json',
        'x-zapper-api-key': api_key
    }
    payload = {'query': test_query}
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=10)
        print(f"📡 Response Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'errors' not in data:
                print("✅ API connection successful!")
                return True
            else:
                print(f"❌ GraphQL errors: {data['errors']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def print_defi_report(summary: Dict[str, Any], defi_positions: List[DeFiPosition]):
    """Print a formatted DeFi portfolio report"""
    print("=" * 80)
    print("ZAPPER DeFi PORTFOLIO REPORT")
    print("=" * 80)
    print(f"Generated: {summary['timestamp']}")
    print(f"Addresses: {', '.join(summary['addresses'])}")
    print(f"Chains: {', '.join(summary['chain_names']) if summary['chain_names'] else 'N/A'}")
    print(f"Chain IDs: {', '.join(map(str, summary['chain_ids'])) if summary['chain_ids'] else 'N/A'}")
    print(f"Total DeFi Portfolio Value: ${summary['total_value_usd']:.2f}")
    print(f"Total Positions: {summary['position_count']}")
    print(f"Unique Apps: {summary['unique_apps']}")

    if summary['meta_type_summary']:
        print("\n" + "-" * 80)
        print("POSITION TYPES SUMMARY")
        print("-" * 80)
        sorted_meta_types = sorted(summary['meta_type_summary'].items(),
                                 key=lambda x: x[1]['total_usd'], reverse=True)
        for meta_type, info in sorted_meta_types:
            print(f"{meta_type:12s} | {info['count']:3d} positions | ${info['total_usd']:>10.2f}")

    print("\n" + "-" * 80)
    print("DeFi POSITIONS DETAILS")
    print("-" * 80)

    defi_positions.sort(key=lambda x: x.balance_usd, reverse=True)
    for i, position in enumerate(defi_positions, 1):
        print(f"{i:3d}. {position}")
        if position.underlying_tokens and position.balance_usd > 1.0:
            for token_info in position.underlying_tokens[:3]:
                if position.position_type == 'contract-position':
                    token_data = token_info.get('token', {})
                    meta_type = token_info.get('metaType', '')
                    symbol = token_data.get('symbol', 'Unknown')
                    balance_usd = token_data.get('balanceUSD', 0)
                    if balance_usd > 0.01:
                        print(f"     └─ {meta_type}: {symbol} (${balance_usd:.2f})")
                else:
                    symbol = token_info.get('symbol', 'Unknown')
                    balance_usd = token_info.get('balanceUSD', 0)
                    if balance_usd > 0.01:
                        print(f"     └─ {symbol} (${balance_usd:.2f})")

    print("\n" + "-" * 80)
    print("SUMMARY BY APPLICATION")
    print("-" * 80)

    sorted_apps = sorted(summary['app_summary'].items(),
                        key=lambda x: x[1]['total_usd'], reverse=True)
    for app_key, info in sorted_apps:
        print(f"{info['app_name']:20s} | {info['network']:10s} | {info['count']:2d} pos | ${info['total_usd']:>10.2f}")

def get_claimable_positions(defi_positions: List[DeFiPosition]) -> List[DeFiPosition]:
    """Filter positions to show only claimable rewards"""
    return [pos for pos in defi_positions if pos.meta_type == 'CLAIMABLE' and pos.balance_usd > 0.01]

def print_claimable_report(claimable_positions: List[DeFiPosition]):
    """Print a report of claimable rewards"""
    if not claimable_positions:
        print("\n🎯 No claimable rewards found.")
        return

    total_claimable = sum(pos.balance_usd for pos in claimable_positions)
    print(f"\n🎯 CLAIMABLE REWARDS SUMMARY")
    print("=" * 50)
    print(f"Total Claimable Value: ${total_claimable:.2f}")
    print(f"Number of Claimable Positions: {len(claimable_positions)}")
    print("\nClaimable Positions:")
    print("-" * 50)

    claimable_positions.sort(key=lambda x: x.balance_usd, reverse=True)
    for i, position in enumerate(claimable_positions, 1):
        print(f"{i:2d}. {position}")
        for token_info in position.underlying_tokens:
            token_data = token_info.get('token', {})
            symbol = token_data.get('symbol', 'Unknown')
            balance = token_data.get('balance', 0)
            balance_usd = token_data.get('balanceUSD', 0)
            if balance_usd > 0.01:
                print(f"     └─ {balance:.6f} {symbol} (${balance_usd:.2f})")

def main():
    """Main function to demonstrate the Zapper API usage"""
    if API_KEY == 'YOUR_API_KEY':
        print("❌ Error: Please set your Zapper API key in the API_KEY variable")
        print("Get your API key from: https://zapper.xyz/")
        print("Visit: https://protocol.zapper.xyz/docs/api/ for documentation")
        sys.exit(1)

    if not test_api_connection(API_KEY):
        print("\n💡 Troubleshooting tips:")
        print("1. Verify your API key is correct")
        print("2. Check if you have sufficient credits in your Zapper account")
        print("3. Visit https://protocol.zapper.xyz/dashboard to check your account")
        print("4. Try again in a few minutes if rate limited")
        sys.exit(1)

    wallet_addresses = ['0x834D9c7688ca1C10479931dE906bCC44879A0446']
    chain_ids = [1]  # Ethereum mainnet

    try:
        print("\n🔄 Initializing Zapper API client...")
        zapper = ZapperAPI(API_KEY)
        print("📊 Fetching portfolio data...")

        defi_positions = zapper.get_defi_positions(wallet_addresses, chain_ids)
        summary = zapper.get_defi_summary(wallet_addresses, chain_ids)

        print_defi_report(summary, defi_positions)

        claimable_positions = get_claimable_positions(defi_positions)
        print_claimable_report(claimable_positions)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
