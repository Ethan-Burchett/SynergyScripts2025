from flask import Flask, request, send_file
import pandas as pd
from io import BytesIO
from datetime import datetime
import os
import json
import re

def load_mappings():
    from dotenv import load_dotenv # type: ignore
    load_dotenv()
    THERAPIST_NAME_MAP = json.loads(os.getenv("THERAPIST_NAME_MAP_ENV", "{}")) # load secrets from .env and parse into json
    CPT_CATEGORY_MAP = json.loads(os.getenv("CPT_CATEGORY_MAP_ENV", "{}"))
    return THERAPIST_NAME_MAP, CPT_CATEGORY_MAP

# Date of Service Report for CPT Units
# Creates sum of CPT codes by person by unit
def process_CPT_report(file, therapist_map, cpt_map):
    # Load and process the Excel file
        df = pd.read_excel(file, sheet_name="Detailed Data", engine="openpyxl")
        df.columns = df.columns.str.strip()

        df["Date"] = pd.to_datetime(df["Date of Service"], errors="coerce")
        # df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time + pd.Timedelta(days=7))  ## working 1 week offset, but starts on monday
        df["Week"] = df["Date"] - pd.to_timedelta(df["Date"].dt.weekday + 1, unit="D")

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
        unmapped = cleaned[cleaned["Category"].isna()].copy() ## keep track of unmapped cpt codes
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

        # if not unmapped.empty:
        #     print("⚠️ Unmapped CPT Codes:")
        #     print(unmapped[["CPT Code", "Treating Therapist"]].drop_duplicates())

        return summary,unmapped
       
def create_ouput_CPT_excel(summary,type,unmapped):
     # Save cleaned data to memory
        output = BytesIO() ## create a file that exists in memory - no disk required - gets deleted at the end

        # Write grouped data to memory
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            summary.to_excel(writer, index=False, sheet_name="Grouped Totals")

            # keep track of unmapped codes
            if unmapped is not None and not unmapped.empty:
                columns = ["Date", "Treating Therapist", "CPT Code", "Units BIlled"]
                for col in columns:
                    if col not in unmapped.columns:
                        unmapped[col] = None  # fill with blank if missing
                unmapped[columns].to_excel(writer, index=False, sheet_name="Unmapped CPT Codes")

        output.seek(0)
        start_date = summary["Week"].min().replace("/", "-")  # e.g., 05/20/2025 → 05-20-2025
        end_date = summary["Week"].max().replace("/", "-")
        report_date = datetime.now().strftime("%Y-%m-%d")

        filename = f"synergy_{type}_report_week_of_{start_date}_generated_{report_date}.xlsx"

        return send_file(output, download_name=filename, as_attachment=True)




## REVENUE
# Process Date
def process_revenue_report(file, therapist_map, cpt_map):
    # Load and process the Excel file
        df = pd.read_excel(file, sheet_name="Detailed Data", engine="openpyxl")
        df.columns = df.columns.str.strip()

        ## get date from filename
        # print(file.filename) #CPT Report - 07-13-25 to 07-19-25.xlsx
        match = re.match(r"CPT Report - (\d{2}-\d{2}-\d{2}) to \d{2}-\d{2}-\d{2}\.xlsx", file.filename)

        if match:
            start_date_str = match.group(1)
            print("start date: " + start_date_str)  # ➝ "07-13-25"

        df["Week"] = pd.to_datetime(start_date_str)
        #df["Date"] = pd.to_datetime(df["Date of Service"], errors="coerce")
        # df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time + pd.Timedelta(days=7))  ## working 1 week offset, but starts on monday
        #df["Week"] = df["Date"] - pd.to_timedelta(df["Date"].dt.weekday + 1, unit="D") ## I think this works for one week only. 

       # Define columns we want to keep
        expected_cols = ["Date of Service", "Treating Therapist", "CPT Code", "Units BIlled", "$ Billed", "$ Allowed", "Provider Paid"]
        missing = [col for col in expected_cols if col not in df.columns]
        if missing:
            return f"Missing required columns: {', '.join(missing)}", 400
        
        # Keep only the columns we care about
        cleaned = df[["Week", "Treating Therapist", "CPT Code", "Units BIlled", "Provider Paid","$ Billed", "$ Allowed",]].copy()
        cleaned["Units BIlled"] = pd.to_numeric(cleaned["Units BIlled"], errors="coerce").fillna(0).astype(int)
        cleaned["Treating Therapist"] = cleaned["Treating Therapist"].map(therapist_map)

        cleaned["Category"] = cleaned["CPT Code"].map(cpt_map)
        unmapped = cleaned[cleaned["Category"].isna()].copy()

        overpaid_rows = cleaned[cleaned["Provider Paid"] > cleaned["$ Allowed"]]

        cleaned = cleaned.dropna(subset=["Category"])  # Drop any unmapped codes

        summary = cleaned.groupby(["Week", "Treating Therapist", "Category"], as_index=False).agg({
            "Provider Paid": "sum",
            "$ Billed": "sum",
            "$ Allowed": "sum"
        })

        summary["Week"] = pd.to_datetime(summary["Week"]).dt.strftime("%m/%d/%Y")

        ## sorting ## 
        # Sort by last name extracted from "Treating Therapist"
        # Sort by last name (A–Z) and week (oldest to newest)
        summary["_LastName"] = summary["Treating Therapist"].str.split(",").str[0].str.strip()
        summary["Week_dt"] = pd.to_datetime(summary["Week"])

        summary = summary.sort_values(by=["_LastName", "Week_dt"], ascending=[True, True])
        summary = summary.drop(columns=["_LastName", "Week_dt"])

        # if not unmapped.empty:
            # print("⚠️ Unmapped CPT Codes:")
            # print(unmapped[["CPT Code", "Treating Therapist"]].drop_duplicates())

        return summary,unmapped,overpaid_rows
       
def create_ouput_revenue_excel(summary,type,unmapped,overpaid_rows):
     # Save cleaned data to memory
        output = BytesIO() ## create a file that exists in memory - no disk required - gets deleted at the end

        # Write grouped data to memory
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            summary.to_excel(writer, index=False, sheet_name="Grouped Totals")

            # keep track of unmapped codes
            if unmapped is not None and not unmapped.empty:
                # print(unmapped.columns)
                columns = ["Treating Therapist", "CPT Code", "Units BIlled"]
                for col in columns:
                    if col not in unmapped.columns:
                        unmapped[col] = None  # fill with blank if missing
                unmapped[columns].to_excel(writer, index=False, sheet_name="Unmapped CPT Codes")

            # keep track of unmapped codes
            if overpaid_rows is not None and not overpaid_rows.empty:
                # print(overpaid_rows.columns)
                columns = overpaid_rows.columns
                for col in columns:
                    if col not in unmapped.columns:
                        unmapped[col] = None  # fill with blank if missing
                unmapped[columns].to_excel(writer, index=False, sheet_name="Overpaid Provider vs Allowed")


        output.seek(0)
        start_date = summary["Week"].min().replace("/", "-")  # e.g., 05/20/2025 → 05-20-2025
        end_date = summary["Week"].max().replace("/", "-")
        report_date = datetime.now().strftime("%Y-%m-%d")

        filename = f"synergy_{type}_report_week_of_{start_date}_generated_{report_date}.xlsx"

        return send_file(output, download_name=filename, as_attachment=True)

