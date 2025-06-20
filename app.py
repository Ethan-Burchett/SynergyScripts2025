from flask import Flask, request, send_file, redirect, url_for
import pandas as pd
import tempfile
import os
from datetime import datetime
from io import BytesIO

app = Flask(__name__)

CPT_CATEGORY_MAP = {
    "97110": "Spokane",
    "97112": "Spokane",
    "97530": "Spokane",
    "97535": "Spokane",
    "97140": "Spokane",
    "97163": "Spokane",
    "97162": "Spokane",
    "97161": "Spokane",
    "97127": "Spokane",
    "97165": "Spokane",
    "97166": "Spokane",
    "97167": "Spokane",
    "97168": "Spokane",
    "97164": "Spokane",
    "S9982": "Spokane",
    
    "G0283": "EStim",
    "97014": "EStim",
    "97032": "EStim",
    
    "97026": "Red light",
    
    "0101T": "Stemwave",
    "6A930": "Stemwave"
}

THERAPIST_NAME_MAP = {
    "Vera Janelle Axtell": "Axtell, Janelle",
    "Mary Carpenter": "Carpenter, Mary",
    "Charles Depner":"Depner, Chuck",
    "Arch Harrison": "Harrison, Arch",
    "Brad Lyons": "Lyons, Brad",
    "Kathryn Matsubuchi":"Matsubuchi, Kathryn",
    "Robyn Moug":"Moug, Robyn",
    "Cheryl Smith": "Smith, Cheryl",

}


# HTML_FORM = """
# <!doctype html>
# <title>Upload Excel File</title>
# <h2>Upload Revenue by CPT Code Report</h2>
# <form method=post enctype=multipart/form-data>
#   <input type=file name=file accept=".xlsx" required>
#   <input type=submit value="Generate Report">
# </form>
# """


HTML_FORM = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Upload Revenue Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f7f8;
            color: #333;
            max-width: 500px;
            margin: 50px auto;
            padding: 30px;
            border-radius: 8px;
            background-color: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h2 {
            text-align: center;
            margin-bottom: 20px;
            color: #2c3e50;
        }
        input[type="file"] {
            display: block;
            margin: 20px auto;
            padding: 10px;
        }
        input[type="submit"] {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 12px 20px;
            font-size: 16px;
            border-radius: 4px;
            display: block;
            margin: 0 auto;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: #2980b9;
        }
    </style>
</head>
<body>
    <h2>Synergy Report Tool</h2>
    <p style="text-align:center; font-size: 1.2em; color: gray;">Generate billing insights from your CPT report</p>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept=".xlsx" required>
        <input type="submit" value="Generate Report">
    </form>
    <p style="text-align:center; font-size: 0.9em; color: gray;">
  Note: Processing may take up to 30 seconds depending on file size.
</p>
</body>
</html>
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
        #df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time.strftime('%Y-%m-%d'))
        #df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time + pd.Timedelta(days=7))
        df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time + pd.Timedelta(days=7))  ## working 1 week offset, but starts on monday
        # df["Week"] = df["Date"] - pd.to_timedelta((df["Date"].dt.weekday + 1) % 7, unit='d')

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
        cleaned["Treating Therapist"] = cleaned["Treating Therapist"].map(THERAPIST_NAME_MAP)


        cleaned["Category"] = cleaned["CPT Code"].map(CPT_CATEGORY_MAP)
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