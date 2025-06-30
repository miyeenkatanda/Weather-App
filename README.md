# Louisville Weather Dashboard

A real-time weather dashboard for Louisville, KY, built with Dash and the Open-Meteo API. The dashboard provides both daily and hourly weather data with interactive visualizations.

## Features

- Real-time weather data from Open-Meteo API
- Daily temperature, wind speed, and humidity trends
- Hourly temperature data
- Support for both metric and imperial units
- Interactive graphs and visualizations
- Mobile-responsive design

## Local Development

1. Clone the repository

```bash
git clone <your-repo-url>
cd <your-repo-name>
```

2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Run the application

```bash
python app.py
```

The application will be available at `http://localhost:8050`

## Deployment

This application is configured for deployment on Render.com:

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Use the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:server`
   - Python Version: 3.9 or later

## Data Sources

- Weather data: [Open-Meteo API](https://open-meteo.com/)
- Map image: Custom Louisville map
- Weather icons: [Flaticon](https://www.flaticon.com/)
