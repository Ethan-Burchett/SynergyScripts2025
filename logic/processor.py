from flask import Flask, request, send_file
import pandas as pd
from io import BytesIO
from datetime import datetime
import os
import json

def load_mappings():
    from dotenv import load_dotenv # type: ignore
    load_dotenv()
    THERAPIST_NAME_MAP = json.loads(os.getenv("THERAPIST_NAME_MAP_ENV", "{}")) # load secrets from .env and parse into json
    CPT_CATEGORY_MAP = json.loads(os.getenv("CPT_CATEGORY_MAP_ENV", "{}"))
    return THERAPIST_NAME_MAP, CPT_CATEGORY_MAP

def process_excel(file, therapist_map, cpt_map):
    # Load and process the Excel file
        df = pd.read_excel(file, sheet_name="Detailed Data", engine="openpyxl")
        df.columns = df.columns.str.strip()

        df["Date"] = pd.to_datetime(df["Date of Service"], errors="coerce")
        df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time + pd.Timedelta(days=7))  ## working 1 week offset, but starts on monday

       # Define columns we want to keep
        expected_cols = ["Date of Service", "Treating Therapist", "CPT Code", "Units BIlled"]
        missing = [col for col in expected_cols if col not in df.columns]
        if missing:
            return f"Missing required columns: {', '.join(missing)}", 400
        
        # Keep only the columns we care about
        cleaned = df[["Week", "Treating Therapist", "CPT Code", "Units BIlled"]].copy()
        cleaned["Units BIlled"] = pd.to_numeric(cleaned["Units BIlled"], errors="coerce").fillna(0).astype(int)
        cleaned["Treating Therapist"] = cleaned["Treating Therapist"].map(therapist_map)


        cleaned["Category"] = cleaned["CPT Code"].map(cpt_map)
        cleaned = cleaned.dropna(subset=["Category"])  # Drop any unmapped codes

        summary = cleaned.groupby(["Week", "Treating Therapist", "Category"], as_index=False).agg({
            "Units BIlled": "sum"
        })
        summary["Week"] = pd.to_datetime(summary["Week"]).dt.strftime("%m/%d/%Y")

        ## sorting ## 
        # Sort by last name extracted from "Treating Therapist"
        # Sort by last name (A–Z) and week (oldest to newest)
        summary["_LastName"] = summary["Treating Therapist"].str.split(",").str[0].str.strip()
        summary["Week_dt"] = pd.to_datetime(summary["Week"])

        summary = summary.sort_values(by=["_LastName", "Week_dt"], ascending=[True, True])
        summary = summary.drop(columns=["_LastName", "Week_dt"])

        return summary
       
def create_ouput_excel(summary):
     # Save cleaned data to memory
        output = BytesIO() ## create a file that exists in memory - no disk required - gets deleted at the end

        # Write grouped data to memory
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            summary.to_excel(writer, index=False, sheet_name="Grouped Totals")
            
        output.seek(0)
        start_date = summary["Week"].min().replace("/", "-")  # e.g., 05/20/2025 → 05-20-2025
        end_date = summary["Week"].max().replace("/", "-")
        report_date = datetime.now().strftime("%Y-%m-%d")

        filename = f"synergy_report_{start_date}_to_{end_date}_generated_{report_date}.xlsx"

        return send_file(output, download_name=filename, as_attachment=True)