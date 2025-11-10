import streamlit as st
import pandas as pd
import nsepython as ns
from datetime import datetime
import matplotlib.pyplot as plt

st.title("Nifty Indices Data Extraction and Visualization")

# Define the indices
indices = ['NIFTY 50', 'NIFTY MIDCAP 150', 'NIFTY SMALLCAP 250']

# Function to extract data
def extract_data():
    st.write("Extracting data... This may take a few minutes.")
    current_year = datetime.now().year
    data_dict = {}
    for index in indices:
        st.write(f"Fetching data for {index}...")
        data_list = []
        for year in range(current_year - 5, current_year + 1):
            start = datetime(year, 1, 1)
            end = datetime(year, 12, 31)
            if end > datetime.now():
                end = datetime.now()
            start_str = start.strftime('%d-%b-%Y')
            end_str = end.strftime('%d-%b-%Y')
            data = ns.index_history(index, start_str, end_str)
            data_list.append(data)
        data = pd.concat(data_list, ignore_index=True)
        data = data.drop_duplicates(subset=['HistoricalDate'])
        data['Date'] = pd.to_datetime(data['HistoricalDate'], format='%d %b %Y')
        data = data.set_index('Date').sort_index()
        data_dict[index] = data
    return data_dict

# Button to extract data
if st.button("Extract Data"):
    data_dict = extract_data()
    st.session_state['data'] = data_dict
    st.success("Data extracted successfully!")

# If data is available, visualize
if 'data' in st.session_state:
    data_dict = st.session_state['data']

    # Combine data
    combined_df = pd.DataFrame()
    for index, df in data_dict.items():
        combined_df[f"{index.replace(' ', '_')}_CLOSE"] = df['CLOSE']

    # Calculate moving averages
    for col in combined_df.columns:
        combined_df[f"{col}_MA50"] = combined_df[col].rolling(window=50).mean()
        combined_df[f"{col}_MA200"] = combined_df[col].rolling(window=200).mean()

    st.write("Combined Data Preview:")
    st.dataframe(combined_df.tail())

    # Plot
    st.write("Combined Chart with Moving Averages:")
    fig, ax = plt.subplots(figsize=(14, 8))
    for col in combined_df.columns:
        if 'CLOSE' in col:
            ax.plot(combined_df.index, combined_df[col], label=col)
        elif 'MA50' in col:
            ax.plot(combined_df.index, combined_df[col], linestyle='--', label=col)
        elif 'MA200' in col:
            ax.plot(combined_df.index, combined_df[col], linestyle=':', label=col)

    ax.set_xlabel('Date')
    ax.set_ylabel('Index Value')
    ax.set_title('Nifty Indices CLOSE Prices with 50-day and 200-day Moving Averages')
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # Download options
    for index, df in data_dict.items():
        csv = df.to_csv()
        st.download_button(
            label=f"Download {index} Data",
            data=csv,
            file_name=f"{index.replace(' ', '_')}_last_5_years.csv",
            mime='text/csv'
        )
else:
    st.write("Click 'Extract Data' to start.")
