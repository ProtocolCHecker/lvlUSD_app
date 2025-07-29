import streamlit as st
import time
from datetime import datetime
import pandas as pd
import io
import sys
from contextlib import redirect_stdout
from get_lvlUSD_slvlUSD_supply import (
    web3 as web3_supply,
    lvlUSD_contract,
    slvlUSD_contract
)
from get_lvlUSD_portfolio_zapper import (
    ZapperAPI,
    test_api_connection,
    get_claimable_positions
)
from get_aUSDC_info import (
    web3 as web3_aUSDC,
    aEthUSDC_contract,
    variableDebtEthUSDC_contract
)
from get_lvlusd_curve_pool import (
    web3 as web3_curve,
    lvlusd_usdc_pool_contract,
    lvlusd_slvlusd_pool_contract
)
from lvlusd_pendle_situation import get_lvlusd_pendle_situation
from slvlusd_pendle_situation import get_slvlusd_pendle_situation
from stakehouse_situation import get_stakehouse_situation

# Configure Streamlit page
st.set_page_config(
    page_title="lvlUSD Ecosystem Dashboard",
    page_icon="📊",
    layout="wide"
)

def capture_print_output(func):
    """Decorator to capture print output from a function"""
    def wrapper(*args, **kwargs):
        f = io.StringIO()
        with redirect_stdout(f):
            func(*args, **kwargs)
        return f.getvalue()
    return wrapper

# Wrapped versions of the original functions to capture their print output
@capture_print_output
def get_lvlusd_pendle_situation_wrapped():
    return get_lvlusd_pendle_situation()

@capture_print_output
def get_slvlusd_pendle_situation_wrapped():
    return get_slvlusd_pendle_situation()

@capture_print_output
def get_stakehouse_situation_wrapped():
    return get_stakehouse_situation()

def check_web3_connections():
    """Verify all Web3 connections are active"""
    connections = {
        "Supply Check": web3_supply,
        "aUSDC Check": web3_aUSDC,
        "Curve Pool Check": web3_curve
    }
    
    with st.spinner("Checking Web3 connections..."):
        all_connected = True
        for name, connection in connections.items():
            if not connection.is_connected():
                st.error(f"❌ {name} Web3 connection failed")
                all_connected = False
        
        if all_connected:
            st.success("✅ All Web3 connections successful")
        else:
            st.warning("⚠️ Some Web3 connections failed - data may be incomplete")
    
    return all_connected

def get_supply_info():
    """Get and display lvlUSD/slvlUSD supply information"""
    with st.spinner("Fetching lvlUSD/slvlUSD supply data..."):
        lvlUSD_supply = lvlUSD_contract.functions.totalSupply().call() / 10**18
        slvlUSD_supply = slvlUSD_contract.functions.totalSupply().call() / 10**18
        current_percentage = (slvlUSD_supply / lvlUSD_supply) * 100
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total lvlUSD Supply", f"{lvlUSD_supply:,.2f}")
        with col2:
            st.metric("Total slvlUSD Supply", f"{slvlUSD_supply:,.2f}")
        with col3:
            st.metric("slvlUSD/lvlUSD Ratio", f"{current_percentage:.2f}%")
        
        return {
            "lvlUSD_supply": lvlUSD_supply,
            "slvlUSD_supply": slvlUSD_supply,
            "percentage": current_percentage
        }

def get_collateral_composition():
    """Get collateral composition from Zapper"""
    with st.expander("Collateral Composition (Zapper)", expanded=True):
        API_KEY = 'd4039e1b-6ff5-4931-903e-9ea82316c187'
        wallet_addresses = ['0x834D9c7688ca1C10479931dE906bCC44879A0446']
        
        if not test_api_connection(API_KEY):
            st.error("Zapper API connection failed - skipping collateral composition")
            return None
        
        try:
            zapper = ZapperAPI(API_KEY)
            defi_positions = zapper.get_defi_positions(wallet_addresses)
            
            # Create DataFrame for positions
            positions_data = []
            for pos in defi_positions:
                positions_data.append({
                    "App": pos.app_name,
                    "Network": pos.network,
                    "Position": pos.display_label or pos.symbol,
                    "Value (USD)": pos.balance_usd,
                    "Type": pos.position_type
                })
            
            df_positions = pd.DataFrame(positions_data)
            
            # Display positions table
            st.subheader("DeFi Positions")
            st.dataframe(
                df_positions.sort_values("Value (USD)", ascending=False),
                column_config={
                    "Value (USD)": st.column_config.NumberColumn(format="$%.2f")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Display summary metrics
            total_value = df_positions["Value (USD)"].sum()
            unique_apps = df_positions["App"].nunique()
            
            col1, col2 = st.columns(2)
            col1.metric("Total Portfolio Value", f"${total_value:,.2f}")
            col2.metric("Unique Protocols", unique_apps)
            
            # Claimable rewards
            claimable_positions = get_claimable_positions(defi_positions)
            if claimable_positions:
                st.subheader("Claimable Rewards")
                claimable_data = []
                for pos in claimable_positions:
                    for token in pos.underlying_tokens:
                        token_data = token.get('token', {})
                        claimable_data.append({
                            "App": pos.app_name,
                            "Asset": token_data.get('symbol', 'Unknown'),
                            "Amount": token_data.get('balance', 0),
                            "Value (USD)": token_data.get('balanceUSD', 0)
                        })
                
                df_claimable = pd.DataFrame(claimable_data)
                st.dataframe(
                    df_claimable.sort_values("Value (USD)", ascending=False),
                    column_config={
                        "Value (USD)": st.column_config.NumberColumn(format="$%.2f")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No claimable rewards found")
            
            return {
                "total_value": total_value,
                "positions": df_positions,
                "claimable": claimable_positions
            }
        except Exception as e:
            st.error(f"Error fetching Zapper data: {e}")
            return None

def get_aUSDC_situation():
    """Get aUSDC collateral situation"""
    with st.expander("aUSDC Collateral Situation", expanded=True):
        with st.spinner("Fetching aUSDC data..."):
            current_supply = aEthUSDC_contract.functions.totalSupply().call() / 10**6
            current_borrow = variableDebtEthUSDC_contract.functions.totalSupply().call() / 10**6
            current_liquidity = current_supply - current_borrow
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Supply", f"${current_supply:,.2f}")
            col2.metric("Total Borrow", f"${current_borrow:,.2f}")
            col3.metric("Available Liquidity", f"${current_liquidity:,.2f}")
            
            # Utilization chart
            utilization_data = pd.DataFrame({
                "Metric": ["Supply", "Borrow", "Available"],
                "Value (USD)": [current_supply, current_borrow, current_liquidity]
            })
            
            st.bar_chart(
                utilization_data.set_index("Metric"),
                color="#FF4B4B"
            )
            
            return {
                "total_supply": current_supply,
                "total_borrow": current_borrow,
                "available_liquidity": current_liquidity
            }

def get_curve_pools():
    """Get lvlUSD Curve pool information"""
    with st.expander("lvlUSD Curve Pool Situation", expanded=True):
        with st.spinner("Fetching Curve pool data..."):
            # lvlUSD/USDC Pool
            st.subheader("lvlUSD/USDC Pool")
            usdc_balances = lvlusd_usdc_pool_contract.functions.get_balances().call()
            usdc_lvlUSD = usdc_balances[0] / (10 ** 6)
            usdc_USDC = usdc_balances[1] / (10 ** 18)
            
            col1, col2 = st.columns(2)
            col1.metric("lvlUSD Balance", f"{usdc_lvlUSD:,.2f}")
            col2.metric("USDC Balance", f"{usdc_USDC:,.2f}")
            
            # lvlUSD/slvlUSD Pool
            st.subheader("lvlUSD/slvlUSD Pool")
            slvl_balances = [
                lvlusd_slvlusd_pool_contract.functions.balances(i).call() 
                for i in range(2)
            ]
            slvl_lvlUSD = slvl_balances[0] / (10 ** 18)
            slvl_slvlUSD = slvl_balances[1] / (10 ** 18)
            
            col1, col2 = st.columns(2)
            col1.metric("lvlUSD Balance", f"{slvl_lvlUSD:,.2f}")
            col2.metric("slvlUSD Balance", f"{slvl_slvlUSD:,.2f}")
            
            return {
                "lvlUSD/USDC": {"lvlUSD": usdc_lvlUSD, "USDC": usdc_USDC},
                "lvlUSD/slvlUSD": {"lvlUSD": slvl_lvlUSD, "slvlUSD": slvl_slvlUSD}
            }

def display_market_data(data, title):
    """Improved function to display market data"""
    with st.expander(title, expanded=False):
        if not data or not data.strip():
            st.warning("No data available for this market")
            return
        
        # Split into individual markets
        market_sections = [section for section in data.split("\n\n") if section.strip()]
        
        for section in market_sections:
            if not section.startswith("Market:"):
                continue
                
            lines = [line.strip() for line in section.split("\n") if line.strip()]
            if not lines:
                continue
                
            market_name = lines[0].split(": ")[1]
            st.subheader(market_name)
            
            # Create columns for metrics
            col1, col2, col3 = st.columns(3)
            col4, col5 = st.columns(2)
            
            # Parse and display metrics
            for line in lines[1:]:
                if ": " in line:
                    key, value = line.split(": ", 1)
                    
                    # Format the key for display
                    display_key = key.strip()
                    
                    # Special handling for different metrics
                    if "Total Supply" in key:
                        col1.metric("Total Supply", value.split(" (")[0], help=value)
                    elif "Total Borrow" in key:
                        col2.metric("Total Borrow", value.split(" (")[0], help=value)
                    elif "Available Liquidity" in key:
                        col3.metric("Available Liquidity", value.split(" (")[0], help=value)
                    elif "Supply APY" in key:
                        col4.metric("Supply APY", value)
                    elif "Borrow APY" in key:
                        col5.metric("Borrow APY", value)
                    elif "Utilization" in key:
                        st.progress(float(value.replace('%', ''))/100, text=f"Utilization: {value}")
                    elif key.strip() == "Rewards":
                        st.markdown("**Rewards:**")
                        # The next lines are the rewards
                        reward_lines = [l for l in lines[lines.index(line)+1:] if l.startswith("  ")]
                        for reward in reward_lines:
                            st.markdown(f"- {reward.strip()}")
                    else:
                        st.text(f"{display_key}: {value}")

def main():
    """Main function to generate the Streamlit dashboard"""
    st.title("lvlUSD Ecosystem Dashboard")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize session state for refresh
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = None
    
    # Add refresh button
    if st.button("Refresh Data"):
        st.session_state.last_refresh = datetime.now()
        st.rerun()
    
    if st.session_state.last_refresh:
        st.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check connections
    check_web3_connections()
    
    # Main dashboard sections
    tab1, tab2, tab3 = st.tabs(["Overview", "Collateral", "Markets"])
    
    with tab1:
        # Supply information
        st.header("Supply Information")
        get_supply_info()
        
    
    with tab2:

        # aUSDC situation
        st.header("aUSDC Collateral")
        get_aUSDC_situation()

        # Collateral composition
        st.header("Collateral Composition")
        get_collateral_composition()
    
    with tab3:

        # Curve pools
        st.header("Curve Pools")
        get_curve_pools()

        # Pendle markets
        st.header("Pendle Markets")
        
        col1, col2 = st.columns(2)
        with col1:
            with st.spinner("Fetching lvlUSD Pendle data..."):
                try:
                    lvlusd_data = get_lvlusd_pendle_situation_wrapped()
                    display_market_data(lvlusd_data, "lvlUSD Pendle Markets")
                except Exception as e:
                    st.error(f"Failed to fetch lvlUSD Pendle data: {e}")
        
        with col2:
            with st.spinner("Fetching slvlUSD Pendle data..."):
                try:
                    slvlusd_data = get_slvlusd_pendle_situation_wrapped()
                    display_market_data(slvlusd_data, "slvlUSD Pendle Markets")
                except Exception as e:
                    st.error(f"Failed to fetch slvlUSD Pendle data: {e}")
        
        # Stakehouse markets
        st.header("Stakehouse Markets")
        with st.spinner("Fetching Stakehouse data..."):
            try:
                stakehouse_data = get_stakehouse_situation_wrapped()
                display_market_data(stakehouse_data, "Stakehouse USDC Vaults")
            except Exception as e:
                st.error(f"Failed to fetch Stakehouse data: {e}")

if __name__ == "__main__":
    main()