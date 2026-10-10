
import json
import os
import re
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "students.json"

load_dotenv(BASE_DIR / ".env")

HF_TOKEN = os.getenv("HF_TOKEN")

MODEL_ID = "openai/gpt-oss-120b"

client = None

if HF_TOKEN:
    client = InferenceClient(
        provider="auto",
        api_key=HF_TOKEN,
        timeout=60
    )


# --------------------------------------------------
# 2. JSON FILE OPERATIONS
# --------------------------------------------------

def load_data():
    """Read student records from the JSON file."""
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_data(data):
    """Save updated student records to the JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def refresh_counts(data):
    """Recalculate present days and recorded days."""
    for student in data["students"]:
        records = student["attendance"]

        student["days_present"] = sum(
            1 for status in records.values()
            if status == "present"
        )

        # Only dates with a recorded status count.
        student["total_days"] = len(records)


def attendance_percentage(student):
    """Calculate percentage using recorded attendance."""
    total = student["total_days"]

    if total == 0:
        return 0.0

    return round(student["days_present"] / total * 100, 2)


def find_student(data, roll_no):
    """Find a student using their roll number."""
    for student in data["students"]:
        if str(student["roll_no"]) == str(roll_no):
            return student

    return None


# --------------------------------------------------
# 3. HUGGING FACE MODEL
# --------------------------------------------------

def interpret_request(user_input):
    """
    Convert a natural-language request into a JSON action.
    The model interprets the request; Python performs
    all attendance calculations and file modifications.
    """

    if client is None:
        raise RuntimeError(
            "HF_TOKEN is missing. Add your token to the .env file."
        )

    system_prompt = """
You are the request interpreter for a student attendance
management system.

Convert the user's request into exactly one valid JSON object.
Do not return Markdown, code fences, or explanations.

Use this schema:
{
  "action": "percentage | check | mark | remove | class_average | list",
  "roll_no": "student roll number or null",
  "date": "YYYY-MM-DD or null",
  "status": "present | absent | null"
}

Rules:
1. percentage means calculate one student's attendance percentage.
2. check means check attendance on a particular date.
3. mark means set attendance on a date. Set status to
   present or absent based on the user's explicit instruction.
4. remove means delete that date's attendance record.
5. class_average means calculate the class average percentage.
6. list means return the attendance information for all students.
7. Never invent roll numbers, dates, or attendance statuses.
8. Convert dates such as "8 October 2026" into "2026-10-08".
9. If a required detail is missing or ambiguous, use null
   for that field.
10. Never calculate percentages. Python will calculate them.
11. Only use the action names listed in the schema.
"""

    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        max_tokens=200,
        temperature=0.1
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("The model returned an empty response.")

    # Support a response accidentally wrapped in code fences.
    content = content.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    # Extract the JSON object if extra text was returned.
    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("The model did not return valid JSON.")

    result = json.loads(content[start:end + 1])

    allowed_actions = {
        "percentage", "check", "mark",
        "remove", "class_average", "list"
    }

    if result.get("action") not in allowed_actions:
        raise ValueError("The model returned an unsupported action.")

    return result


# --------------------------------------------------
# 4. VALIDATION
# --------------------------------------------------

def validate_date(data, date_text):
    """Check date format and assignment date range."""
    if not isinstance(date_text, str):
        return False

    try:
        requested_date = date.fromisoformat(date_text)
        start = date.fromisoformat(data["date_range"]["start"])
        end = date.fromisoformat(data["date_range"]["end"])

        return start <= requested_date <= end

    except ValueError:
        return False


def error_response(message):
    return {
        "success": False,
        "message": message
    }


# --------------------------------------------------
# 5. ATTENDANCE OPERATIONS
# --------------------------------------------------

def process_request(data, request):
    action = request.get("action")
    roll_no = request.get("roll_no")
    requested_date = request.get("date")
    status = request.get("status")

    # List every student's attendance.
    if action == "list":
        refresh_counts(data)

        students = []

        for student in data["students"]:
            students.append({
                "name": student["name"],
                "roll_no": student["roll_no"],
                "days_present": student["days_present"],
                "total_days": student["total_days"],
                "attendance_percentage":
                    attendance_percentage(student),
                "attendance": student["attendance"]
            })

        return {
            "success": True,
            "action": "list",
            "students": students
        }

    # Calculate the class average from individual percentages.
    if action == "class_average":
        refresh_counts(data)

        percentages = [
            attendance_percentage(student)
            for student in data["students"]
        ]

        if not percentages:
            average = 0.0
        else:
            average = round(sum(percentages) / len(percentages), 2)

        return {
            "success": True,
            "action": "class_average",
            "students_count": len(percentages),
            "individual_percentages": percentages,
            "class_average_percentage": average
        }

    # Other actions require a valid student roll number.
    if roll_no is None:
        return error_response(
            "Please specify the student's roll number."
        )

    student = find_student(data, roll_no)

    if student is None:
        return error_response(
            f"No student found with roll number {roll_no}."
        )

    # Calculate one student's percentage.
    if action == "percentage":
        refresh_counts(data)

        return {
            "success": True,
            "action": "percentage",
            "name": student["name"],
            "roll_no": student["roll_no"],
            "days_present": student["days_present"],
            "total_days": student["total_days"],
            "attendance_percentage":
                attendance_percentage(student)
        }

    # Check, mark, and remove need a valid date.
    if not validate_date(data, requested_date):
        return error_response(
            "Provide a valid date between 2026-10-08 "
            "and 2026-10-14 in the requested date format."
        )

    records = student["attendance"]

    # Check attendance for a particular date.
    if action == "check":
        current_status = records.get(requested_date, "not_recorded")

        return {
            "success": True,
            "action": "check",
            "name": student["name"],
            "roll_no": student["roll_no"],
            "date": requested_date,
            "status": current_status
        }

    # Mark or update attendance.
    if action == "mark":
        if status not in ("present", "absent"):
            return error_response(
                "Specify whether the student was present or absent."
            )

        records[requested_date] = status

        refresh_counts(data)
        save_data(data)

        return {
            "success": True,
            "action": "mark",
            "name": student["name"],
            "roll_no": student["roll_no"],
            "date": requested_date,
            "status": status,
            "days_present": student["days_present"],
            "total_days": student["total_days"],
            "attendance_percentage":
                attendance_percentage(student),
            "message": "Attendance saved to students.json."
        }

    # Remove the record for a particular date.
    if action == "remove":
        if requested_date not in records:
            return error_response(
                "No attendance record exists for that date."
            )

        del records[requested_date]

        refresh_counts(data)
        save_data(data)

        return {
            "success": True,
            "action": "remove",
            "name": student["name"],
            "roll_no": student["roll_no"],
            "date": requested_date,
            "days_present": student["days_present"],
            "total_days": student["total_days"],
            "attendance_percentage":
                attendance_percentage(student),
            "message": "Attendance record removed from students.json."
        }

    return error_response(
        "I could not identify a supported attendance operation."
    )


# --------------------------------------------------
# 6. MAIN TERMINAL LOOP
# --------------------------------------------------

def main():
    print("=" * 48)
    print("   AI ATTENDANCE MANAGEMENT SYSTEM")
    print("   Powered by Hugging Face")
    print("=" * 48)

    if client is None:
        print(
            "\nERROR: HF_TOKEN is missing. "
            "Check your .env file."
        )
        return

    try:
        data = load_data()
    except (OSError, json.JSONDecodeError) as error:
        print(f"\nCould not read students.json: {error}")
        return

    refresh_counts(data)

    print("\nDate range: 8 October 2026 - 14 October 2026")
    print("Type 'exit' to close the program.")

    print("\nExample requests:")
    print("- Show attendance percentage for roll number 101")
    print("- Was roll number 102 present on 10 October 2026?")
    print("- Mark roll number 101 absent on 12 October 2026")
    print("- Remove attendance for roll number 103 on 8 October 2026")
    print("- Calculate the class attendance average")
    print("- Show all students")

    while True:
        user_input = input("\nEnter your request: ").strip()

        if user_input.lower() in ("exit", "quit"):
            print("Attendance system closed.")
            break

        if not user_input:
            continue

        try:
            request = interpret_request(user_input)
            result = process_request(data, request)

            # Display the result as formatted JSON.
            print("\nResponse:")
            print(json.dumps(result, indent=2))

        except Exception as error:
            # Avoid crashing the application on API or parsing errors.
            print(json.dumps({
                "success": False,
                "message": (
                    "Could not process the request. "
                    "Check your model access, internet connection, "
                    "token permissions, and request wording."
                ),
                "error": str(error)
            }, indent=2))


if __name__ == "__main__":
    main()
