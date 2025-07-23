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