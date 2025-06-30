import openmeteo_requests
import pandas as pd
import numpy as np
import requests_cache
from retry_requests import retry
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import dash_bootstrap_components as dbc
import os
import glob
from datetime import datetime

# Set pandas display option for 2 decimal float precision
pd.set_option("display.float_format", "{:.2f}".format)

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


# FUNCTION TO GET THE DATA


def get_weather_data(latitude=38.2542, longitude=-85.7594, unit_system="imperial"):
    """
    Fetch weather data from Open-Meteo API for the specified location.
    Default coordinates are for Louisville, KY.

    Args:
        latitude (float): Location latitude
        longitude (float): Location longitude
        unit_system (str): Unit system ('imperial' or 'metric')

    Returns:
        tuple: (daily_dataframe, hourly_dataframe) containing weather data
    """
    today = date.today()
    url = "https://api.open-meteo.com/v1/forecast"
    
    # Set units based on the selected system
    temp_unit = "fahrenheit" if unit_system == "imperial" else "celsius"
    wind_unit = "mph" if unit_system == "imperial" else "kmh"
    precip_unit = "inch" if unit_system == "imperial" else "mm"
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "temperature_2m_mean",
            "wind_speed_10m_mean",
            "wind_speed_10m_min",
            "wind_speed_10m_max",
            "relative_humidity_2m_mean",
            "relative_humidity_2m_max",
            "relative_humidity_2m_min",
            "precipitation_sum",
            "rain_sum",
        ],
        "hourly": [
            "temperature_2m",
        ],
        "timezone": "America/New_York",
        "past_days": 31,
        "wind_speed_unit": wind_unit,
        "temperature_unit": temp_unit,
        "precipitation_unit": precip_unit,
    }

    print("Fetching daily weather data from Open-Meteo API...")
    try:
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        print("Data fetched successfully.")

        daily = response.Daily()
        daily_data = {
            "date": pd.date_range(
                start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left",
            ).date
        }

        # Assign values with rounding
        daily_data["temperature_2m_max"] = np.round(
            daily.Variables(0).ValuesAsNumpy(), 2
        )
        daily_data["temperature_2m_min"] = np.round(
            daily.Variables(1).ValuesAsNumpy(), 2
        )
        daily_data["temperature_2m_mean"] = np.round(
            daily.Variables(2).ValuesAsNumpy(), 2
        )
        daily_data["wind_speed_10m_mean"] = np.round(
            daily.Variables(3).ValuesAsNumpy(), 2
        )
        daily_data["wind_speed_10m_min"] = np.round(
            daily.Variables(4).ValuesAsNumpy(), 2
        )
        daily_data["wind_speed_10m_max"] = np.round(
            daily.Variables(5).ValuesAsNumpy(), 2
        )
        daily_data["relative_humidity_2m_mean"] = np.round(
            daily.Variables(6).ValuesAsNumpy(), 2
        )
        daily_data["relative_humidity_2m_max"] = np.round(
            daily.Variables(7).ValuesAsNumpy(), 2
        )
        daily_data["relative_humidity_2m_min"] = np.round(
            daily.Variables(8).ValuesAsNumpy(), 2
        )
        daily_data["precipitation_sum"] = np.round(
            daily.Variables(9).ValuesAsNumpy(), 2
        )
        daily_data["rain_sum"] = np.round(daily.Variables(10).ValuesAsNumpy(), 2)

        daily_dataframe = pd.DataFrame(data=daily_data)

        hourly = response.Hourly()
        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left",
            )
        }
        hourly_data["temperature_2m"] = hourly.Variables(0).ValuesAsNumpy()
        hourly_dataframe = pd.DataFrame(data=hourly_data)
        
        # Save files with unit system in filename
        hourly_dataframe.to_csv(f"{unit_system}_hourly_data_{today}.csv", index=False)
        daily_dataframe.to_csv(f"{unit_system}_daily_data_{today}.csv", index=False)

    except Exception as e:
        print(f"Error fetching data: {e}")
        print("Creating a dummy DataFrame for demonstration.")
        dates = [today - timedelta(days=i) for i in range(31, 0, -1)] + [
            today + timedelta(days=i) for i in range(7)
        ]
        
        # Adjust dummy data ranges based on unit system
        if unit_system == "imperial":
            temp_max_range = (60, 90)
            temp_min_range = (40, 70)
            temp_mean_range = (50, 80)
            wind_range = (5, 20)
            precip_range = (0, 1)
        else:
            temp_max_range = (15, 32)
            temp_min_range = (4, 21)
            temp_mean_range = (10, 27)
            wind_range = (8, 32)  # km/h
            precip_range = (0, 25)  # mm
            
        dummy_data = {
            "date": dates,
            "temperature_2m_max": np.random.uniform(temp_max_range[0], temp_max_range[1], len(dates)),
            "temperature_2m_min": np.random.uniform(temp_min_range[0], temp_min_range[1], len(dates)),
            "temperature_2m_mean": np.random.uniform(temp_mean_range[0], temp_mean_range[1], len(dates)),
            "wind_speed_10m_mean": np.random.uniform(wind_range[0], wind_range[1], len(dates)),
            "wind_speed_10m_min": np.random.uniform(0, wind_range[0], len(dates)),
            "wind_speed_10m_max": np.random.uniform(wind_range[0], wind_range[1] * 1.5, len(dates)),
            "relative_humidity_2m_mean": np.random.uniform(60, 90, len(dates)),
            "relative_humidity_2m_max": np.random.uniform(70, 100, len(dates)),
            "relative_humidity_2m_min": np.random.uniform(40, 70, len(dates)),
            "precipitation_sum": np.random.uniform(0, precip_range[1], len(dates)),
            "rain_sum": np.random.uniform(0, precip_range[1] * 0.8, len(dates)),
        }
        daily_dataframe = pd.DataFrame(dummy_data)
        daily_dataframe["date"] = pd.to_datetime(daily_dataframe["date"])

        # Save dummy data with unit system in filename
        daily_dataframe.to_csv(f"{unit_system}_daily_data_{today}.csv", index=False)

    return daily_dataframe, hourly_dataframe


# Add this function after the imports
def cleanup_old_data_files():
    """Delete CSV files older than today."""
    today = datetime.now().date()

    # Delete daily data files for both unit systems
    for unit in ['imperial', 'metric']:
        daily_files = glob.glob(f"{unit}_daily_data_*.csv")
        for file in daily_files:
            try:
                file_date = datetime.strptime(
                    file.split("_")[3].split(".")[0], "%Y-%m-%d"
                ).date()
                if file_date < today:
                    os.remove(file)
                    print(f"Deleted old file: {file}")
            except Exception as e:
                print(f"Error processing file {file}: {e}")

        # Delete hourly data files
        hourly_files = glob.glob(f"{unit}_hourly_data_*.csv")
        for file in hourly_files:
            try:
                file_date = datetime.strptime(
                    file.split("_")[3].split(".")[0], "%Y-%m-%d"
                ).date()
                if file_date < today:
                    os.remove(file)
                    print(f"Deleted old file: {file}")
            except Exception as e:
                print(f"Error processing file {file}: {e}")


# ---------- LOAD OR FETCH DATA ---------- #
today = date.today()
if os.path.exists(f"daily_data_{today}.csv") and os.path.exists(
    f"hourly_data_{today}.csv"
):
    print("Loading daily data from cache...")
    daily_dataframe = pd.read_csv(f"daily_data_{today}.csv")
    daily_dataframe["date"] = pd.to_datetime(daily_dataframe["date"])
    hourly_dataframe = pd.read_csv(f"hourly_data_{today}.csv")
    hourly_dataframe["date"] = pd.to_datetime(hourly_dataframe["date"])
else:
    print("Fetching daily data from Open-Meteo API...")
    daily_dataframe, hourly_dataframe = get_weather_data()
    daily_dataframe["date"] = pd.to_datetime(daily_dataframe["date"])
    hourly_dataframe["date"] = pd.to_datetime(hourly_dataframe["date"])
    cleanup_old_data_files()


unique_days = hourly_dataframe[
    hourly_dataframe["date"].dt.date >= pd.to_datetime(today).date()
]["date"].dt.date.unique()


def create_hourly_graphs(selected_date):
    """
    Create hourly temperature graph for the selected date.

    Args:
        selected_date (date): The date to display hourly data for

    Returns:
        plotly.graph_objects.Figure: The hourly temperature graph
    """
    filtered = hourly_dataframe[hourly_dataframe["date"].dt.date == selected_date]
    fig_temp = px.line(
        filtered,
        x="date",
        y="temperature_2m",
        labels={
            "temperature_2m": "Temperature (°F)",
            "date": "Time",
            "variable": "Metric",
        },
        template="plotly_dark",
        title=f"Hourly Temperature – {selected_date}",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    return fig_temp


# --- 2. Initialize the Dash Application ---
external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css",
]

app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = "Weather Dashboard"


# --- 3. Define the Layout of the Dashboard ---
app.layout = html.Div(
    style={"backgroundColor": "#e0f2f7", "padding": "20px", "minHeight": "100vh"},
    children=[
        # Logo and Title Row
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.Img(
                                src=app.get_asset_url("weather_logo.png"),
                                style={
                                    "height": "60px",
                                    "marginRight": "5px",
                                    "verticalAlign": "middle",
                                },
                            ),
                            html.H1(
                                "Louisville Weather Dashboard",
                                className="text-primary mb-4 d-inline-block",
                                style={"margin": "0", "verticalAlign": "middle"},
                            ),
                        ],
                        className="text-center",
                    ),
                    width=12,
                ),
            ],
            className="mb-4",
        ),
        html.Div(
            style={
                "width": "95%",
                "maxWidth": "1400px",
                "margin": "auto",
                "padding": "25px",
                "backgroundColor": "#ffffff",
                "borderRadius": "12px",
                "boxShadow": "0 6px 12px rgba(0,0,0,0.15)",
            },
            children=[
                # Louisville Map
                html.Div(
                    html.Img(
                        src=app.get_asset_url("louisville_map.png"),
                        style={
                            "width": "100%",
                            "height": "auto",
                            "display": "block",
                            "margin": "0 auto 20px auto",
                            "borderRadius": "8px",
                            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                        },
                    ),
                    className="text-center",
                ),
                # title
                html.H1(
                    "Louisville Daily Weather Overview",
                    style={
                        "textAlign": "center",
                        "color": "#212121",
                        "fontSize": "2.5em",
                    },
                ),
                # Date Picker for Daily Summary
                html.Div(
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "marginBottom": "30px",
                        "gap": "15px",
                    },
                    children=[
                        html.Label(
                            "Select a Date for Daily Summary:",
                            style={
                                "fontSize": "1.3em",
                                "color": "#333",
                                "fontWeight": "bold",
                            },
                        ),
                        dcc.DatePickerSingle(
                            id="date-picker-daily",
                            min_date_allowed=daily_dataframe["date"].min(),
                            max_date_allowed=daily_dataframe["date"].max(),
                            # initial date should be today's date
                            initial_visible_month=date.today(),
                            date=date.today(),
                            display_format="YYYY-MM-DD",
                            style={
                                "border": "1px solid #ccc",
                                "borderRadius": "5px",
                                "padding": "5px",
                            },
                        ),
                    ],
                ),
                html.Hr(),
                html.Br(),
                # Add unit system state
                dcc.Store(id='unit-system-store', data='imperial'),

                # Add radio button after the date picker
                html.Div(
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "marginBottom": "30px",
                        "gap": "15px",
                    },
                    children=[
                        html.Label(
                            "Unit System:",
                            style={
                                "fontSize": "1.3em",
                                "color": "#333",
                                "fontWeight": "bold",
                            },
                        ),
                        dcc.RadioItems(
                            id='unit-system-selector',
                            options=[
                                {'label': ' Imperial (°F, mph, in)', 'value': 'imperial'},
                                {'label': ' Metric (°C, km/h, mm)', 'value': 'metric'}
                            ],
                            value='imperial',
                            inline=False,
                            style={'fontSize': '1.1em'}
                        ),
                    ],
                ),
                html.Hr(),
                html.Br(),
                # Current Day Summary Cards
                html.Div(id="daily-summary-cards", style={"marginBottom": "40px"}),
                html.Hr(),
                html.Br(),
                html.H2(
                    "Daily Weather Trends (Past 31 Days + Forecast)",
                    style={
                        "textAlign": "center",
                        "color": "#333",
                        "marginBottom": "25px",
                        "fontSize": "1.8em",
                    },
                ),
          
                # Temperature Trend Chart
                html.Div(
                    style={
                        "marginBottom": "30px",
                        "backgroundColor": "#f0f8ff",
                        "padding": "20px",
                        "borderRadius": "8px",
                        "boxShadow": "0 2px 4px rgba(0,0,0,0.08)",
                    },
                    children=[
                        html.H3(
                            id="temp-trend-title",
                            children="Daily Temperature Trends",
                            style={
                                "textAlign": "center",
                                "color": "#424242",
                                "marginBottom": "15px",
                            },
                        ),
                        dcc.Graph(id="temp-trend-chart"),
                    ],
                ),
                html.Hr(),
                html.Br(),
                # Boxplots Card
                html.Div(
                    style={
                        "marginBottom": "30px",
                        "backgroundColor": "#f0f8ff",
                        "padding": "20px",
                        "borderRadius": "8px",
                        "boxShadow": "0 2px 4px rgba(0,0,0,0.08)",
                    },
                    children=[
                        html.H3(
                            "Temperature Distribution Analysis",
                            style={
                                "textAlign": "center",
                                "color": "#424242",
                                "marginBottom": "15px",
                            },
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Graph(id="boxplot-temp-max"), width=12, md=4
                                ),
                                dbc.Col(
                                    dcc.Graph(id="boxplot-temp-min"), width=12, md=4
                                ),
                                dbc.Col(
                                    dcc.Graph(id="boxplot-temp-mean"), width=12, md=4
                                ),
                            ],
                            className="mb-4",
                        ),
                    ],
                ),
                html.Hr(),
                html.Br(),
                # Wind Speed Trend Chart
                html.Div(
                    style={
                        "marginBottom": "30px",
                        "backgroundColor": "#f0f8ff",
                        "padding": "20px",
                        "borderRadius": "8px",
                        "boxShadow": "0 2px 4px rgba(0,0,0,0.08)",
                    },
                    children=[
                        html.H3(
                            id="wind-trend-title",
                            children="Daily Wind Speed Trends",
                            style={
                                "textAlign": "center",
                                "color": "#424242",
                                "marginBottom": "15px",
                            },
                        ),
                        dcc.Graph(id="wind-trend-chart"),
                    ],
                ),
                html.Hr(),
                html.Br(),
                # Humidity Trend Chart
                html.Div(
                    style={
                        "backgroundColor": "#f0f8ff",
                        "padding": "20px",
                        "borderRadius": "8px",
                        "boxShadow": "0 2px 4px rgba(0,0,0,0.08)",
                        "marginBottom": "30px",
                    },
                    children=[
                        html.H3(
                            "Daily Relative Humidity Trends (%)",
                            style={
                                "textAlign": "center",
                                "color": "#424242",
                                "marginBottom": "15px",
                            },
                        ),
                        dcc.Graph(id="humidity-trend-chart"),
                    ],
                ),
                html.Hr(),
                html.Br(),
                # Hourly Weather Section
                html.Div(
                    style={
                        "backgroundColor": "#f0f8ff",
                        "padding": "20px",
                        "borderRadius": "8px",
                        "boxShadow": "0 2px 4px rgba(0,0,0,0.08)",
                    },
                    children=[
                        html.H3(
                            "Hourly Weather Analysis",
                            style={
                                "textAlign": "center",
                                "color": "#424242",
                                "marginBottom": "15px",
                            },
                        ),
                        html.H4(
                            "Select a Date to View Hourly Temperature",
                            className="text-center text-primary mb-3",
                            style={"fontSize": "1.2em"},
                        ),
                        dcc.Tabs(
                            id="hourly-tabs",
                            value=str(unique_days[0]),
                            children=[
                                dcc.Tab(
                                    label=str(day),
                                    value=str(day),
                                    style={'padding': '10px'},
                                    selected_style={
                                        'padding': '10px',
                                        'backgroundColor': '#e0f2f7',
                                        'borderTop': '3px solid #2196F3'
                                    }
                                )
                                for day in unique_days[:7]
                            ],
                            style={'marginBottom': '20px'}
                        ),
                        html.Div(id="hourly-tab-content"),
                    ],
                ),
            ],
        ),
        # Footer with attribution
        html.Footer(
            html.Div(
                [
                    html.P(
                        [
                            "Weather icons created by ",
                            html.A(
                                "Freepik",
                                href="https://www.flaticon.com/free-icons/weather",
                                target="_blank",
                                style={"color": "#666"},
                            ),
                            " - ",
                            html.A(
                                "Flaticon",
                                href="https://www.flaticon.com",
                                target="_blank",
                                style={"color": "#666"},
                            ),
                        ],
                        style={
                            "textAlign": "center",
                            "color": "#666",
                            "fontSize": "0.8em",
                            "marginTop": "20px",
                        },
                    ),
                ],
                style={"padding": "10px"},
            ),
        ),
    ],
)


# --- 4. Implement Callbacks for Interactivity ---


# Callbacks
@app.callback(Output("hourly-tab-content", "children"), 
             [Input("hourly-tabs", "value"),
              Input("unit-system-store", "data")])
def update_hourly_graphs(selected_date, unit_system):
    """
    Update hourly temperature graph when a new date is selected in the tabs.

    Args:
        selected_date (str): The selected date string
        unit_system (str): The selected unit system ('imperial' or 'metric')

    Returns:
        dash.html.Div: The updated hourly temperature graph
    """
    selected = pd.to_datetime(selected_date).date()
    
    # Get the correct temperature unit label
    temp_unit = "°F" if unit_system == "imperial" else "°C"
    
    # Load the correct data file
    if not os.path.exists(f"{unit_system}_hourly_data_{today}.csv"):
        print(f"Fetching data for {unit_system} units...")
        _, hourly_dataframe = get_weather_data(unit_system=unit_system)
    else:
        print(f"Loading {unit_system} hourly data from cache...")
        hourly_dataframe = pd.read_csv(f"{unit_system}_hourly_data_{today}.csv")
        hourly_dataframe["date"] = pd.to_datetime(hourly_dataframe["date"])

    filtered = hourly_dataframe[hourly_dataframe["date"].dt.date == selected]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=filtered["date"],
            y=filtered["temperature_2m"],
            mode="lines+markers",
            name=f"Temperature ({temp_unit})",
            line=dict(color="red"),
        )
    )
    
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title=f"Temperature ({temp_unit})",
        template="plotly_dark",
        title=f"Hourly Temperature on {selected} ({temp_unit})",
        height=400,
        margin=dict(t=50, b=20, l=40, r=20),
    )
    
    return dbc.Row([dbc.Col(dcc.Graph(figure=fig), md=12)])


@app.callback(
    [Output('daily-summary-cards', 'children'),
     Output('temp-trend-chart', 'figure'),
     Output('wind-trend-chart', 'figure'),
     Output('humidity-trend-chart', 'figure'),
     Output('boxplot-temp-max', 'figure'),
     Output('boxplot-temp-min', 'figure'),
     Output('boxplot-temp-mean', 'figure')],
    [Input('date-picker-daily', 'date'),
     Input('unit-system-store', 'data')]
)
def update_dashboard(selected_date_str, unit_system):
    """
    Update all dashboard components when a new date is selected or unit system changes.
    """
    global daily_dataframe, hourly_dataframe
    
    # Check if we need to load or fetch new data
    if not os.path.exists(f"{unit_system}_daily_data_{today}.csv") or not os.path.exists(f"{unit_system}_hourly_data_{today}.csv"):
        print(f"Fetching data for {unit_system} units...")
        daily_dataframe, hourly_dataframe = get_weather_data(unit_system=unit_system)
        cleanup_old_data_files()
    else:
        print(f"Loading {unit_system} data from cache...")
        daily_dataframe = pd.read_csv(f"{unit_system}_daily_data_{today}.csv")
        daily_dataframe["date"] = pd.to_datetime(daily_dataframe["date"]).dt.date
        hourly_dataframe = pd.read_csv(f"{unit_system}_hourly_data_{today}.csv")
        hourly_dataframe["date"] = pd.to_datetime(hourly_dataframe["date"])

    # Get unit labels based on unit system
    temp_unit = "°F" if unit_system == "imperial" else "°C"
    wind_unit = "mph" if unit_system == "imperial" else "km/h"
    precip_unit = "in" if unit_system == "imperial" else "mm"

    # Convert the selected date string to a date object
    selected_date = pd.to_datetime(selected_date_str).date()

    # Filter for the selected day's summary
    selected_day_data = daily_dataframe[daily_dataframe["date"] == selected_date]

    # --- Daily Summary Cards ---
    summary_cards_children = []
    
    if not selected_day_data.empty:
        data_row = selected_day_data.iloc[0]

        # --- KPI Variables ---
        max_temp = data_row["temperature_2m_max"]
        max_wind = data_row["wind_speed_10m_max"]
        mean_humidity = data_row["relative_humidity_2m_mean"]

        summary_cards_children = [
            html.Div(
                className="text-center",
                children=[
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            [
                                                html.I(
                                                    className="bi bi-cloud-fill me-2"
                                                ),
                                                f"Max Temp ({temp_unit})",
                                            ]
                                        ),
                                        dbc.CardBody(
                                            [
                                                html.H2(
                                                    f"{max_temp:.2f}",
                                                    className="card-text text-center",
                                                )
                                            ]
                                        ),
                                    ],
                                    color="dark",
                                    inverse=True,
                                    className="shadow-sm rounded-3 mb-3",
                                )
                            ),
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            [
                                                html.I(className="bi bi-wind me-2"),
                                                f"Max Wind ({wind_unit})",
                                            ]
                                        ),
                                        dbc.CardBody(
                                            [
                                                html.H2(
                                                    f"{max_wind:.2f}",
                                                    className="card-text text-center",
                                                )
                                            ]
                                        ),
                                    ],
                                    color="info",
                                    inverse=True,
                                    className="shadow-sm rounded-3 mb-3",
                                )
                            ),
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            [
                                                html.I(className="bi bi-moisture me-2"),
                                                "Mean Humidity (%)",
                                            ]
                                        ),
                                        dbc.CardBody(
                                            [
                                                html.H2(
                                                    f"{mean_humidity:.2f}",
                                                    className="card-text text-center",
                                                )
                                            ]
                                        ),
                                    ],
                                    color="danger",
                                    inverse=True,
                                    className="shadow-sm rounded-3 mb-3",
                                )
                            ),
                        ]
                    ),
                ],
            )
        ]
    else:
        summary_cards_children = html.P(
            f"No data available for {selected_date}.",
            style={"textAlign": "center", "color": "#888", "fontSize": "1.2em"},
        )

    # --- Temperature Trend Chart ---
    temp_fig = go.Figure()
    temp_fig.add_trace(
        go.Scatter(
            x=daily_dataframe["date"],
            y=daily_dataframe["temperature_2m_max"],
            mode="lines+markers",
            name="Max Temp",
            line=dict(color="red"),
        )
    )
    temp_fig.add_trace(
        go.Scatter(
            x=daily_dataframe["date"],
            y=daily_dataframe["temperature_2m_min"],
            mode="lines+markers",
            name="Min Temp",
            line=dict(color="blue"),
        )
    )
    temp_fig.add_trace(
        go.Scatter(
            x=daily_dataframe["date"],
            y=daily_dataframe["temperature_2m_mean"],
            mode="lines+markers",
            name="Mean Temp",
            line=dict(color="purple", dash="dot"),
        )
    )

    # Highlight selected date
    if not selected_day_data.empty:
        temp_fig.add_vline(
            x=selected_date,
            line_width=2,
            line_dash="dash",
            line_color="green",
        )

    temp_fig.update_layout(
        xaxis_title="Date",
        yaxis_title=f"Temperature ({temp_unit})",
        hovermode="x unified",
        template="ggplot2",
        height=400,
        margin=dict(t=50, b=20, l=40, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    # --- Wind Speed Trend Chart ---
    wind_fig = go.Figure()
    wind_fig.add_trace(
        go.Scatter(
            x=daily_dataframe["date"],
            y=daily_dataframe["wind_speed_10m_max"],
            mode="lines+markers",
            name="Max Wind",
            line=dict(color="orange"),
        )
    )
    wind_fig.add_trace(
        go.Scatter(
            x=daily_dataframe["date"],
            y=daily_dataframe["wind_speed_10m_mean"],
            mode="lines+markers",
            name="Mean Wind",
            line=dict(color="green", dash="dot"),
        )
    )
    wind_fig.add_trace(
        go.Scatter(
            x=daily_dataframe["date"],
            y=daily_dataframe["wind_speed_10m_min"],
            mode="lines+markers",
            name="Min Wind",
            line=dict(color="teal"),
        )
    )

    # Highlight selected date
    if not selected_day_data.empty:
        wind_fig.add_vline(
            x=selected_date,
            line_width=2,
            line_dash="dash",
            line_color="green",
        )

    wind_fig.update_layout(
        xaxis_title="Date",
        yaxis_title=f"Wind Speed ({wind_unit})",
        hovermode="x unified",
        template="ggplot2",
        height=400,
        margin=dict(t=50, b=20, l=40, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    # --- Humidity Trend Chart ---
    humidity_fig = go.Figure()
    humidity_fig.add_trace(
        go.Scatter(
            x=daily_dataframe["date"],
            y=daily_dataframe["relative_humidity_2m_max"],
            mode="lines+markers",
            name="Max Humidity",
            line=dict(color="darkred"),
        )
    )
    humidity_fig.add_trace(
        go.Scatter(
            x=daily_dataframe["date"],
            y=daily_dataframe["relative_humidity_2m_mean"],
            mode="lines+markers",
            name="Mean Humidity",
            line=dict(color="darkblue", dash="dot"),
        )
    )
    humidity_fig.add_trace(
        go.Scatter(
            x=daily_dataframe["date"],
            y=daily_dataframe["relative_humidity_2m_min"],
            mode="lines+markers",
            name="Min Humidity",
            line=dict(color="darkgreen"),
        )
    )

    # Highlight selected date
    if not selected_day_data.empty:
        humidity_fig.add_vline(
            x=selected_date,
            line_width=2,
            line_dash="dash",
            line_color="green",
        )

    humidity_fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Relative Humidity (%)",
        hovermode="x unified",
        template="ggplot2",
        height=400,
        margin=dict(t=50, b=20, l=40, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    # --- Box Plots ---
    box_temp_max = go.Figure()
    box_temp_max.add_trace(
        go.Box(y=daily_dataframe["temperature_2m_max"], name=f"Temp Max ({temp_unit})")
    )
    box_temp_max.update_layout(
        title=f"Temperature Max ({temp_unit})",
        height=300,
        margin=dict(t=50, b=20, l=40, r=20),
        template="plotly_dark",
    )

    box_temp_min = go.Figure()
    box_temp_min.add_trace(
        go.Box(y=daily_dataframe["temperature_2m_min"], name=f"Temp Min ({temp_unit})")
    )
    box_temp_min.update_layout(
        title=f"Temperature Min ({temp_unit})",
        height=300,
        margin=dict(t=50, b=20, l=40, r=20),
        template="plotly_dark",
    )

    box_temp_mean = go.Figure()
    box_temp_mean.add_trace(
        go.Box(y=daily_dataframe["temperature_2m_mean"], name=f"Temp Mean ({temp_unit})")
    )
    box_temp_mean.update_layout(
        title=f"Temperature Mean ({temp_unit})",
        height=300,
        margin=dict(t=50, b=20, l=40, r=20),
        template="plotly_dark",
    )

    return (
        summary_cards_children,
        temp_fig,
        wind_fig,
        humidity_fig,
        box_temp_max,
        box_temp_min,
        box_temp_mean,
    )

# Add new callback for unit system change
@app.callback(
    Output('unit-system-store', 'data'),
    Input('unit-system-selector', 'value')
)
def update_unit_system(selected_unit):
    """Update unit system and trigger data refresh"""
    return selected_unit

# Add new callback to update section titles
@app.callback(
    [Output("temp-trend-title", "children"),
     Output("wind-trend-title", "children")],
    Input("unit-system-store", "data")
)
def update_section_titles(unit_system):
    """Update section titles with correct units"""
    temp_unit = "°F" if unit_system == "imperial" else "°C"
    wind_unit = "mph" if unit_system == "imperial" else "km/h"
    return [
        f"Daily Temperature Trends ({temp_unit})",
        f"Daily Wind Speed Trends ({wind_unit})"
    ]

# --- 5. Run the Dash Application ---
if __name__ == "__main__":
    app.run(debug=True)
