from flask import Flask, request, send_file, redirect, url_for, render_template
import pandas as pd
import tempfile
import os
import json
from dotenv import load_dotenv
from datetime import datetime
from io import BytesIO
from logic.processor import load_mappings, process_excel, create_ouput_excel

app = Flask(__name__)

load_dotenv()

# THERAPIST_NAME_MAP = json.loads(os.getenv("THERAPIST_NAME_MAP_ENV", "{}")) # load secrets from .env and parse into json

# CPT_CATEGORY_MAP = json.loads(os.getenv("CPT_CATEGORY_MAP_ENV", "{}"))

THERAPIST_NAME_MAP, CPT_CATEGORY_MAP = load_mappings()

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename.endswith(".xlsx"):
            return "Please upload a valid .xlsx Excel file.", 400

        summary = process_excel(file,THERAPIST_NAME_MAP,CPT_CATEGORY_MAP)

        return create_ouput_excel(summary)

        

    #     # Load and process the Excel file
    #     df = pd.read_excel(file, sheet_name="Detailed Data", engine="openpyxl")
    #     df.columns = df.columns.str.strip()

    #     df["Date"] = pd.to_datetime(df["Date of Service"], errors="coerce")
    #     #df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time.strftime('%Y-%m-%d'))
    #     #df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time + pd.Timedelta(days=7))
    #     df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time + pd.Timedelta(days=7))  ## working 1 week offset, but starts on monday
    #     # df["Week"] = df["Date"] - pd.to_timedelta((df["Date"].dt.weekday + 1) % 7, unit='d')

    #     # 🔍 Add this to debug:
    #     print("DEBUG: Columns in uploaded file:", df.columns.tolist())

    #    # Define columns we want to keep
    #     expected_cols = ["Date of Service", "Treating Therapist", "CPT Code", "Units BIlled"]
    #     missing = [col for col in expected_cols if col not in df.columns]
    #     if missing:
    #         return f"Missing required columns: {', '.join(missing)}", 400
        
    #     # Keep only the columns we care about
    #     cleaned = df[["Week", "Treating Therapist", "CPT Code", "Units BIlled"]].copy()
    #     cleaned["Units BIlled"] = pd.to_numeric(cleaned["Units BIlled"], errors="coerce").fillna(0).astype(int)
    #     cleaned["Treating Therapist"] = cleaned["Treating Therapist"].map(THERAPIST_NAME_MAP)


    #     cleaned["Category"] = cleaned["CPT Code"].map(CPT_CATEGORY_MAP)
    #     cleaned = cleaned.dropna(subset=["Category"])  # Drop any unmapped codes

    #     summary = cleaned.groupby(["Week", "Treating Therapist", "Category"], as_index=False).agg({
    #         "Units BIlled": "sum"
    #     })
    #     summary["Week"] = pd.to_datetime(summary["Week"]).dt.strftime("%m/%d/%Y")

    #     ## sorting ## 
    #     # Sort by last name extracted from "Treating Therapist"
    #     # Sort by last name (A–Z) and week (oldest to newest)
    #     summary["_LastName"] = summary["Treating Therapist"].str.split(",").str[0].str.strip()
    #     summary["Week_dt"] = pd.to_datetime(summary["Week"])

    #     summary = summary.sort_values(by=["_LastName", "Week_dt"], ascending=[True, True])
    #     summary = summary.drop(columns=["_LastName", "Week_dt"])

    #    # Save cleaned data to memory
    #     output = BytesIO() ## create a file that exists in memory - no disk required - gets deleted at the end
        
    #     # Write grouped data to memory
    #     with pd.ExcelWriter(output, engine="openpyxl") as writer:
    #         summary.to_excel(writer, index=False, sheet_name="Grouped Totals")
            
    #     output.seek(0)
    #     start_date = summary["Week"].min().replace("/", "-")  # e.g., 05/20/2025 → 05-20-2025
    #     end_date = summary["Week"].max().replace("/", "-")
    #     report_date = datetime.now().strftime("%Y-%m-%d")

    #     filename = f"synergy_report_{start_date}_to_{end_date}_generated_{report_date}.xlsx"

    #     # filename = f"cleaned_billing_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.xlsx"
    #     return send_file(output, download_name=filename, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)