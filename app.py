from flask import Flask, request, render_template
from datetime import datetime
from io import BytesIO
from logic.processor import load_mappings, process_excel, create_ouput_excel

app = Flask(__name__)

THERAPIST_NAME_MAP, CPT_CATEGORY_MAP = load_mappings()

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename.endswith(".xlsx"):
            return "Please upload a valid .xlsx Excel file.", 400

        report_type = request.form.get("report_type")

        if report_type == "CPT Unit Report":
             summary = process_excel(file,THERAPIST_NAME_MAP,CPT_CATEGORY_MAP)
             print("creating CPT code report")
        
        if report_type == "Revenue Report":
            summary = process_excel(file,THERAPIST_NAME_MAP,CPT_CATEGORY_MAP)
            print("creating revenue report")


        return create_ouput_excel(summary)


    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)