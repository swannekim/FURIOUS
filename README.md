# FURIOUS
FURIOUS: Fully Unified Risk-assessment with Interactive Operational User System for vessels

## How to Run the Project
1. **Open Two Terminals:**  
   One terminal will run the server and the other will run the client.

2. **Server Setup:**

   - Navigate to the `server` folder:
     ```bash
     cd server
     ```
   - Activate the virtual environment:
     ```bash
     source venv/bin/activate
     ```
   - Run the server:
     ```bash
     python3 server.py
     ```

3. **Client Setup:**

   - Navigate to the `client` folder:
     ```bash
     cd client
     ```
   - Start the development server:
     ```bash
     npm run dev
     ```

## Data Availability
Please note that the AIS dataset required to run this project is not included in this repository. The AIS data underlying the findings of our study were provided by the Ministry of Oceans and Fisheries (Republic of Korea) strictly for research purposes under a Non-Disclosure Agreement (NDA). Due to legal and ethical restrictions—including provisions of the Personal Information Protection Act—the data cannot be made publicly available. Even after anonymization, the combination of temporal and geolocation information poses a risk of re-identification of individual vessels.

**Data Access:**
Data are available upon reasonable request from qualified researchers. Interested parties should contact Jong Hwa Baek at jhback@kriso.re.kr. Requests will be referred to the appropriate data access committee at the Ministry, which oversees and approves data access in accordance with its established guidelines.

**Note:**
Without access to the AIS dataset, the code may not run as intended. If you have a substitute or synthetic dataset for testing purposes, you may adjust the configuration settings accordingly.

## License

This project is licensed under the [Creative Commons Attribution 4.0 International License (CC BY 4.0)](http://creativecommons.org/licenses/by/4.0/). See the [LICENSE](LICENSE) file for the full license text.
