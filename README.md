
# HACKATHON-Xpert

**HACKATHON-Xpert** is an AI-powered web application designed to assist participants in hackathons by providing expert guidance, project suggestions, and technical resources. Built using Python, Streamlit, and machine learning models, this platform aims to streamline the hackathon preparation process.

## Features

- **AI-Powered Assistance**: Offers expert advice and project suggestions tailored to hackathon themes.
- **Model Integration**: Utilizes machine learning models to provide insights and recommendations.
- **User-Friendly Interface**: Developed with Streamlit for an interactive and intuitive user experience.

## Project Structure

The repository includes the following key components:

- `app.py`: The main application file that runs the Streamlit app.
- `xpert_ui.py`: Contains the user interface components for the application.
- `make_dummy_model.py`: Script to generate a dummy model for testing purposes.
- `test_load_model.py`: Unit tests to ensure the model loads correctly.
- `requirements.txt`: Lists all the necessary Python packages for the project.
- `setup_env.ps1`: PowerShell script to set up the development environment.
- `model/`: Directory containing the machine learning model files.
- `uploads/`: Directory for user-uploaded files.

## Installation

To set up the project locally, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/ibraheemahmad2511-prog/HACKATHON-Xpert.git
   cd HACKATHON-Xpert
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:

   ```bash
   streamlit run app.py
   ```

## Usage

Once the application is running, navigate to the provided local URL (usually `http://localhost:8501`) in your web browser. The interface will guide you through various features, including receiving project suggestions and expert advice.

## Contributing

Contributions are welcome! If you'd like to enhance the project, please fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License.
