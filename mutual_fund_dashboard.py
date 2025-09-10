import streamlit as st

# Function to safely trigger a rerun using fallback if experimental_rerun is missing
def safe_rerun():
    # Streamlit 1.49.1 removed experimental_rerun; fallback by meta refresh
    try:
        st.experimental_rerun()
    except AttributeError:
        # HTML meta refresh forces page reload immediately
        st.markdown('<meta http-equiv="refresh" content="0">', unsafe_allow_html=True)

# Dummy condition you might have for refresh; replace with your logic
def should_refresh():
    # For example, refresh when user clicks button or a checkbox is checked
    return st.session_state.get("refresh_flag", False)

# Main app code
def main():
    st.title("📊 Mutual Fund Dashboard")

    # Add a checkbox to let user decide to refresh or not
    refresh_request = st.checkbox("Refresh data manually")

    if refresh_request:
        # Set session state flag for refresh
        st.session_state["refresh_flag"] = True
    else:
        st.session_state["refresh_flag"] = False

    # If refresh condition met, clear cache and rerun safely
    if should_refresh():
        # Clear cached data gracefully
        st.cache_data.clear()
        safe_rerun()

    # Example content: Replace this with your dashboard/data logic
    st.write("Welcome to the mutual fund dashboard!")
    st.write("Add your data display and analysis here.")

if __name__ == "__main__":
    main()
