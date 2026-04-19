# Mountain Companion & Avalanche Risk Map

This web application is a comprehensive platform for mountain hikers and outdoor enthusiasts. It serves as an interactive hub combining route planning, real-time weather tracking, community-driven reports, and advanced avalanche risk assessment. By integrating external APIs, digital elevation models (DEM), and user-generated content, the app empowers users to make informed and safe decisions during their mountain expeditions.

## Key Features

*   **Interactive Map & Route Planning:** A dynamic map interface allowing users to explore mountain areas, search for specific peaks, and create, save, and visualize their custom hiking routes.
*   **Community-Driven Markers & Alerts:** Authenticated users can drop custom markers on the map to share real-time field observations, trail conditions, or specific warnings with the rest of the community.
*   **Advanced Avalanche Risk Assessment:** Visualizes potential avalanche danger zones by calculating risk levels based on terrain slope, aspect (derived from DEM data), and current meteorological factors (snow depth, wind, temperature).
*   **Comprehensive Weather Integration:** Fetches real-time and forecasted weather data via the Open-Meteo API, providing crucial information for trip planning.
*   **Live Mountain Cameras:** Integrates live camera feeds directly from the TOPR (Tatrzańskie Ochotnicze Pogotowie Ratunkowe) website to provide real-time visual conditions of key locations like Kasprowy Wierch, Morskie Oko, and Dolina Pięciu Stawów.
*   **Peak Search & Location:** Utilizes the Nominatim API (OpenStreetMap) to allow users to search for specific mountain peaks and automatically pan the map to their coordinates.
*   **Avalanche Statistics:** Calculates distances to known avalanche points and assesses the number of avalanches within a specific radius of a given location.

## Technologies Used

*   **Backend:** Python 3, Flask
*   **Database:** SQLite, SQLAlchemy (ORM)
*   **Geospatial & Data Processing:** Rasterio (DEM processing), Pandas, NumPy
*   **APIs:** 
    *   Open-Meteo API (current and historical weather data)
    *   OpenStreetMap API / Nominatim (map, geocoding and peak search)
    *   Scraping TOPR Cameras (live mountain conditions and avalanche risk data)
*   **Frontend:** HTML, CSS, JavaScript (Leaflet.js for interactive maps)

## Setup & Installation

To run this application locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd PythonLawiny
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up the environment variables:**
    Copy the example environment file and customize it with your own values (especially important for production):
    ```bash
    cp .env.example .env
    ```

5.  **Set up the Database:**
    The application will automatically initialize the SQLite database on the first run.

6.  **Run the application:**
    ```bash
    python main.py
    ```

7.  **Access the application:**
    Open your web browser and navigate to `http://127.0.0.1:5000/`

## Project Structure Highlights

*   `main.py`: The entry point of the Flask application.
*   `__init__.py`: Application factory, configuration setup, and database initialization. Loads settings from `.env`.
*   `routes.py`, `flask_routes/`: Contains all routing logic for web pages, map data, and user accounts.
*   `models.py`: Defines the SQLAlchemy database models (`User`, `Route`, `Marker`).
*   `avalanche_danger.py`: Core logic for calculating avalanche risks based on weather and terrain data.
*   `constants.py`: Centralized file storing hyperparameters and physical constants used in risk calculations.
*   `weather_locations.py`: Configuration file containing URLs to TOPR webcams for different mountain regions.
*   `static/`: Contains CSS, JavaScript, generated map images (`risk_map.png`), and GeoJSON data for hiking trails.
*   `templates/`: Contains HTML templates for the frontend.

## Configuration & Environment Variables

This project follows the 12-Factor App methodology for configuration. All sensitive data and environment-specific settings (like database URIs and secret keys) are loaded from environment variables using `os.environ`. 

For local development, these can be placed in a `.env` file (see `.env.example`). The application gracefully falls back to sensible defaults (like a local SQLite database) if these variables are not provided, ensuring a smooth developer experience.

## Authors

*   [Patryk Blacha](https://github.com/PatrykBlacha)
*   [Karolina Nitsch](https://github.com/kanitsch)