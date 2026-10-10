# AI Attendance Management System

A terminal-based attendance management system built using **Python, Hugging Face AI, and JSON**. The project allows users to manage student attendance using natural-language commands and view attendance statistics directly in the terminal.

## Features

- **AI-Powered Queries:** Interpret attendance requests written in natural language using a Hugging Face language model.
- **Attendance Percentage:** Calculate individual student attendance percentages.
- **Attendance Verification:** Check whether a student was present or absent on a specific date.
- **Mark Attendance:** Mark a student as present or absent for a particular date.
- **Remove Attendance:** Remove an existing attendance record.
- **Class Average:** Calculate the average attendance percentage of the class.
- **Student Records:** Display student information and attendance data.
- **JSON Storage:** Store and update student attendance records in a JSON file.
- **Date Validation:** Manage attendance within the configured date range.

## Technologies Used

- **Python** – Application logic and attendance calculations
- **Hugging Face** – Natural-language query interpretation
- **Hugging Face Inference Providers** – Hosted model inference
- **JSON** – Student data storage
- **python-dotenv** – Environment variable management
- **huggingface_hub** – Connecting Python to Hugging Face models

## Project Structure

```text
Attendance-Management-System/
│
├── app.py              # Main application
├── students.json       # Student and attendance records
├── .env                # API token (not uploaded)
├── .env.example        # Example environment configuration
├── .gitignore          # Files excluded from Git
└── README.md           # Project documentation
```

## Requirements

- Python 3.10 or a compatible version
- A Hugging Face account and an access token with the required inference permissions
- Internet connection for hosted model inference

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/AI-Attendance-Management-System.git
cd AI-Attendance-Management-System
```

Replace `YOUR-USERNAME` with your GitHub username.

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install huggingface_hub python-dotenv
```

### 4. Configure the Environment

Create a `.env` file in the project folder:

```dotenv
HF_TOKEN=your_huggingface_token_here
```

Replace the placeholder with your own Hugging Face token. The token must not be shared or committed to GitHub.

The `.env.example` file provides a template for configuration.

### 5. Run the Application

```bash
python app.py
```

The application starts in the terminal and accepts attendance-related queries.

## Example Queries

Users can enter natural-language requests such as:

```text
Show attendance percentage for roll number 101

Was roll number 102 present on 10 October 2026?

Mark roll number 101 absent on 12 October 2026

Remove attendance for roll number 103 on 8 October 2026

Calculate the class attendance average

Show all students
```

The application interprets the request, processes the relevant attendance data, and displays the result in JSON format. Supported commands depend on the implemented application logic.

## How It Works

1. The user enters a natural-language attendance query.
2. The Hugging Face model interprets the query and identifies the requested action and relevant details.
3. Python validates the request and performs the required operation.
4. Attendance percentages and class statistics are calculated using Python.
5. Updated attendance records are saved to `students.json`.
6. The result is displayed in the terminal as JSON.

**Important:** The AI model interprets the request, while Python handles data validation, calculations, and file updates.

## Data Storage

Student details and attendance records are stored in `students.json`. Attendance records use dates in `YYYY-MM-DD` format and status values such as `present` and `absent`.

The configured attendance date range is **8 October 2026 to 14 October 2026**.

## Security Notes

- Never upload `.env` or expose your Hugging Face access token.
- Keep `.env` listed in `.gitignore`.
- Use `.env.example` to document required environment variables.
- Hosted inference availability depends on your Hugging Face token permissions and available credits.

## Future Improvements

- Add a graphical user interface.
- Generate attendance reports and summaries.
- Export attendance records to CSV.
- Add student search and filtering.
- Improve error handling and validation.

## Author

Developed as a Python-based academic project demonstrating AI integration, file handling, JSON data management, and attendance calculations.
