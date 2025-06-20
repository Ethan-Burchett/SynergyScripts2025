from flask import Flask, request, send_file, redirect, url_for
import pandas as pd
import tempfile
import os
from datetime import datetime
from io import BytesIO

app = Flask(__name__)

HTML_FORM = """
<!doctype html>
<title>Upload Excel File</title>
<h2>Upload Weekly CPT Report</h2>
<form method=post enctype=multipart/form-data>
  <input type=file name=file accept=".xlsx" required>
  <input type=submit value="Generate Weekly Report">
</form>
"""

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename.endswith(".xlsx"):
            return "Please upload a valid .xlsx Excel file.", 400

        # Load and process the Excel file
        df = pd.read_excel(file, sheet_name="Detailed Data", engine="openpyxl")
        df.columns = df.columns.str.strip()

        df["Date"] = pd.to_datetime(df["Date of Service"], errors="coerce")
        df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time.strftime('%Y-%m-%d'))

        # 🔍 Add this to debug:
        print("DEBUG: Columns in uploaded file:", df.columns.tolist())

       # Define columns we want to keep
        expected_cols = ["Date of Service", "Treating Therapist", "CPT Code", "Units BIlled"]
        missing = [col for col in expected_cols if col not in df.columns]
        if missing:
            return f"Missing required columns: {', '.join(missing)}", 400
        
        # Keep only the columns we care about
        cleaned = df[["Week", "Treating Therapist", "CPT Code", "Units BIlled"]].copy()
        cleaned["Units BIlled"] = pd.to_numeric(cleaned["Units BIlled"], errors="coerce").fillna(0).astype(int)

        # Group and sum by therapist + CPT
        summary = cleaned.groupby(["Week", "Treating Therapist", "CPT Code"], as_index=False).agg({
            "Units BIlled": "sum"
            })

       # Save cleaned data to memory
        output = BytesIO() ## create a file that exists in memory - no disk required - gets deleted at the end
        
        # Write grouped data to memory
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            summary.to_excel(writer, index=False, sheet_name="Grouped Totals")
            
        output.seek(0)

        filename = f"cleaned_billing_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.xlsx"
        return send_file(output, download_name=filename, as_attachment=True)

    return HTML_FORM

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)