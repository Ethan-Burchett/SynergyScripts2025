# Synergy Report Tool

This tool allows staff to upload Excel-based CPT reports and automatically generate summarized weekly reports grouped by therapist and CPT category. Built with Flask + Pandas and deployable on [Render](https://render.com).

## Features

- Upload `.xlsx` files from web form
- Clean, group, and sum `Units Billed` by week, therapist, and CPT category
- Sort results by therapist last name and week
- Export a cleaned report in `.xlsx` format

---

## Deployment
-  [SynergyScripts Website](https://synergyscripts225.onrender.com/)

-  [Deployment Dashboard](https://dashboard.render.com/web/srv-d1a7h72dbo4c73c7ph40/deploys/dep-d1adfl3e5dus73eg2s1g?r=2025-06-20%4003%3A38%3A01%7E2025-06-20%4003%3A41%3A13)



# Synergy Report Tool — Local Development Setup & Run

This guide walks you through setting up and running the Synergy Report Tool locally from scratch.

---

## 1. Clone the repository

```bash
git clone https://github.com/Ethan-Burchett/SynergyScripts2025.git
cd synergy-report-tool
```

## 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install dependencies
```bash
pip install -r requirements.txt
```

## 4. Secrets
- CPT codes and employee names are secret and are stored in a .env file - ask the admin for access for local building

--- 

## 5. Start the Flask server
```bash
python3 app.py
```
In terminal go to the dev server address like: http://192.168.0.210:8080 - might be different for you


# Reports 

## CPT Unit Report (Date of Visit)

Purpose: Summarizes the number of CPT units billed per therapist, grouped by CPT category and week.

### How it works:
- Extracts the “Date of Service” from each visit row.
- Determines the week starting date (Sunday) from each date.
- Maps CPT codes to high-level categories using a lookup dictionary.
- Groups the data by week, therapist, and category, and calculates the total units billed.
- Use case: Quickly see how much therapy work was delivered by category, by week, and by provider.

 ## Revenue Report (Process Date)
Purpose: Summarizes financial reimbursement totals using the process date range found in the filename, not per-visit dates.
### How it works:
- Extracts the starting date from the filename and assigns it as the “Week” for all rows.
- Maps CPT codes to categories as above.
- Groups the data by therapist and category, then sums up:
    - Provider Paid
	- Billed
	- Allowed
- Identifies any CPT codes not mapped to a known category (if included) and flags rows where Provider Paid > Allowed.