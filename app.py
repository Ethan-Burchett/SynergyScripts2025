from flask import Flask, request, render_template, flash, redirect, url_for, session
from io import BytesIO
from logic.processor import process_CPT_report, create_ouput_CPT_excel, create_ouput_revenue_excel,process_revenue_report
from logic.validators import is_valid_date_range_filename
from logic.init import load_mappings

app = Flask(__name__)
app.secret_key = "test"

THERAPIST_NAME_MAP, CPT_CATEGORY_MAP = load_mappings()

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename.endswith(".xlsx"):
            flash("⚠️ Please upload a valid .xlsx Excel file.")
            return redirect(url_for("upload_file"))
        if not is_valid_date_range_filename(file.filename):
            flash("⚠️ Invalid Date Range: Your file must start on a Sunday and end on a Saturday (7-day range).")
            return redirect(url_for('upload_file'))

        report_type = request.form.get("report_type")

        if report_type == "CPT Unit Report":
             summary, unmapped = process_CPT_report(file,THERAPIST_NAME_MAP,CPT_CATEGORY_MAP)
            #  print("creating CPT code report")
             session.pop('_flashes', None)  # clear old flash messages
             return create_ouput_CPT_excel(summary,"CPT",unmapped)
        
        if report_type == "Revenue Report":
            summary, unmapped,overpaid_rows = process_revenue_report(file,THERAPIST_NAME_MAP,CPT_CATEGORY_MAP) 
            # print("creating revenue report")
            session.pop('_flashes', None) 
            return create_ouput_revenue_excel(summary,"revenue", unmapped, overpaid_rows)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)