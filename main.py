#!/usr/bin/env python3
"""
Main Dashboard for lvlUSD/slvlUSD Ecosystem Monitoring
Consolidates data from multiple sources into a single comprehensive report
"""

import time
from datetime import datetime
from get_lvlUSD_slvlUSD_supply import (
    web3 as web3_supply,
    lvlUSD_contract,
    slvlUSD_contract,
    lvlUSD_total_supply,
    slvlUSD_total_supply,
    percentage
)
from get_lvlUSD_portfolio_zapper import (
    ZapperAPI,
    test_api_connection,
    print_defi_report,
    print_claimable_report,
    get_claimable_positions
)
from get_aUSDC_info import (
    web3 as web3_aUSDC,
    aEthUSDC_contract,
    variableDebtEthUSDC_contract,
    total_supply as aUSDC_total_supply,
    total_borrow as aUSDC_total_borrow,
    available_liquidity as aUSDC_available_liquidity
)
from get_lvlusd_curve_pool import (
    web3 as web3_curve,
    lvlusd_usdc_pool_contract,
    lvlusd_slvlusd_pool_contract,
    get_token_balances
)
from lvlusd_pendle_situation import get_lvlusd_pendle_situation
from slvlusd_pendle_situation import get_slvlusd_pendle_situation
from stakehouse_situation import get_stakehouse_situation

def print_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"=== {title.upper()} ===")
    print("=" * 80)

def check_web3_connections():
    """Verify all Web3 connections are active"""
    connections = {
        "Supply Check": web3_supply,
        "aUSDC Check": web3_aUSDC,
        "Curve Pool Check": web3_curve
    }
    
    all_connected = True
    for name, connection in connections.items():
        if not connection.is_connected():
            print(f"❌ {name} Web3 connection failed")
            all_connected = False
        else:
            print(f"✅ {name} Web3 connection successful")
    
    return all_connected

def get_supply_info():
    """Get and display lvlUSD/slvlUSD supply information"""
    print_header("lvlUSD & slvlUSD Supply Information")
    
    # Refresh supply data
    lvlUSD_supply = lvlUSD_contract.functions.totalSupply().call() / 10**18
    slvlUSD_supply = slvlUSD_contract.functions.totalSupply().call() / 10**18
    current_percentage = (slvlUSD_supply / lvlUSD_supply) * 100
    
    print(f"Total supply of lvlUSD: {lvlUSD_supply:,.2f}")
    print(f"Total supply of slvlUSD: {slvlUSD_supply:,.2f}")
    print(f"Percentage of slvlUSD over lvlUSD: {current_percentage:.2f}%")
    
    return {
        "lvlUSD_supply": lvlUSD_supply,
        "slvlUSD_supply": slvlUSD_supply,
        "percentage": current_percentage
    }

def get_collateral_composition():
    """Get collateral composition from Zapper"""
    print_header("Collateral Composition (Zapper)")
    
    API_KEY = 'd4039e1b-6ff5-4931-903e-9ea82316c187'
    wallet_addresses = ['0x834D9c7688ca1C10479931dE906bCC44879A0446']
    
    if not test_api_connection(API_KEY):
        print("❌ Zapper API connection failed - skipping collateral composition")
        return None
    
    try:
        zapper = ZapperAPI(API_KEY)
        defi_positions = zapper.get_defi_positions(wallet_addresses)
        summary = zapper.get_defi_summary(wallet_addresses)
        
        print_defi_report(summary, defi_positions)
        
        claimable_positions = get_claimable_positions(defi_positions)
        print_claimable_report(claimable_positions)
        
        return {
            "total_value": summary['total_value_usd'],
            "positions": defi_positions,
            "claimable": claimable_positions
        }
    except Exception as e:
        print(f"❌ Error fetching Zapper data: {e}")
        return None

def get_aUSDC_situation():
    """Get aUSDC collateral situation"""
    print_header("aUSDC Collateral Situation")
    
    # Refresh aUSDC data
    current_supply = aEthUSDC_contract.functions.totalSupply().call() / 10**6
    current_borrow = variableDebtEthUSDC_contract.functions.totalSupply().call() / 10**6
    current_liquidity = current_supply - current_borrow
    
    print(f"Total Supply USD: ${current_supply:,.2f}")
    print(f"Total Borrow USD: ${current_borrow:,.2f}")
    print(f"Available Liquidity: ${current_liquidity:,.2f}")
    
    return {
        "total_supply": current_supply,
        "total_borrow": current_borrow,
        "available_liquidity": current_liquidity
    }

def get_curve_pools():
    """Get lvlUSD Curve pool information"""
    print_header("lvlUSD Curve Pool Situation")
    
    print("\n--- lvlUSD/USDC Pool ---")
    get_token_balances(lvlusd_usdc_pool_contract, 'lvlUSD/USDC Pool', 'get_balances')
    
    print("\n--- lvlUSD/slvlUSD Pool ---")
    get_token_balances(lvlusd_slvlusd_pool_contract, 'lvlUSD/slvlUSD Pool', 'balances')
    
    return {
        "timestamp": datetime.now().isoformat()
    }

def main():
    """Main function to generate the consolidated dashboard"""
    start_time = time.time()
    print_header("LVLUSD ECOSYSTEM DASHBOARD")
    print(f"Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check all connections first
    if not check_web3_connections():
        print("\n⚠️ Some Web3 connections failed - data may be incomplete")
    
    try:
        # 1. Supply information
        supply_data = get_supply_info()
        
        # 2. Collateral composition
        collateral_data = get_collateral_composition()
        
        # 3. aUSDC situation
        aUSDC_data = get_aUSDC_situation()

        # 4. Stakehouse situation
        stakehouse_data = get_stakehouse_situation()
        
        # 5. Curve pools
        curve_data = get_curve_pools()
        
        # 6. Pendle situations
        lvlusd_pendle_data = get_lvlusd_pendle_situation()
        slvlusd_pendle_data = get_slvlusd_pendle_situation()
        
        
    except Exception as e:
        print(f"\n❌ Error generating dashboard: {e}")
    
    execution_time = time.time() - start_time
    print_header("REPORT COMPLETE")
    print(f"Dashboard generated in {execution_time:.2f} seconds")
    print(f"Final update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()