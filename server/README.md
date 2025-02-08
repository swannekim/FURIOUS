# Server

This folder contains the Flask-based server for the FURIOUS application. The server provides several endpoints to process and return ship-related data for risk assessment. It is configured to run in development mode (with debug enabled).

## Prerequisites

- **Python 3.6+**
- The provided virtual environment in the `venv` folder (if you encounter issues, consider recreating it).

## Running the Server

1. **Activate the Provided Virtual Environment:**

   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

2. **Run the Server in Development Mode:**

   With the virtual environment activated, start the server by running:
   ```bash
   python3 server.py
