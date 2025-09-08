# Mutual Fund Dashboard

A Streamlit web application that fetches and displays mutual fund data from Moneycontrol.

## Features
- View various mutual fund categories (Large Cap, Mid Cap, Small Cap, ELSS, etc.)
- Filter funds by AUM, CRISIL rating, and returns
- Download data as CSV
- Responsive design

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/mutual-fund-dashboard.git
   cd mutual-fund-dashboard
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the Streamlit app:
```bash
streamlit run mutual_fund_dashboard.py
```

The app will open in your default web browser at `http://localhost:8501`

## Deployment

### Option 1: Streamlit Cloud (Recommended)
1. Push your code to GitHub
2. Go to [Streamlit Cloud](https://share.streamlit.io/)
3. Click "New app" and connect your GitHub repository
4. Select the repository and main file (`mutual_fund_dashboard.py`)
5. Click "Deploy!"

### Option 2: Local Deployment
```bash
pip install -r requirements.txt
streamlit run mutual_fund_dashboard.py
```

## Contributing
Feel free to submit issues and enhancement requests.

## License
This project is licensed under the MIT License.
