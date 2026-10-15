
import os
import subprocess
import uuid
import shutil
from pathlib import Path

from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "ganti-dengan-kunci-rahasia-acak"

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
OUTPUT_FOLDER = UPLOAD_FOLDER / "converted"


LIBREOFFICE = (
    shutil.which("soffice")
    or r"C:\Program Files\LibreOffice\program\soffice.exe"
)

ALLOWED_EXTENSIONS = {".docx", ".xlsx"}

UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    file = request.files.get("file")

    if not file or not file.filename:
        flash("Pilih file Word atau Excel terlebih dahulu.")
        return redirect(url_for("home"))

    original_name = secure_filename(file.filename)
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        flash("Format yang didukung hanya .docx dan .xlsx.")
        return redirect(url_for("home"))

    job_id = uuid.uuid4().hex
    input_path = UPLOAD_FOLDER / f"{job_id}{extension}"
    output_path = OUTPUT_FOLDER / f"{job_id}.pdf"

    try:
        file.save(input_path)

        result = subprocess.run(
            [
                LIBREOFFICE,
                "-env:UserInstallation=file:///"
                + str((UPLOAD_FOLDER / f"lo_profile_{job_id}").resolve()).replace("\\", "/"),
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(OUTPUT_FOLDER),
                str(input_path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

        if result.returncode != 0 or not output_path.exists():
            app.logger.error("LibreOffice: %s", result.stderr or result.stdout)
            flash("Konversi gagal. Periksa file dan instalasi LibreOffice.")
            return redirect(url_for("home"))

        download_name = Path(original_name).stem + ".pdf"

        return send_file(
            output_path,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/pdf",
        )

    except subprocess.TimeoutExpired:
        flash("Konversi memerlukan waktu terlalu lama. Coba file yang lebih kecil.")
        return redirect(url_for("home"))

    except Exception:
        app.logger.exception("Terjadi kesalahan saat konversi.")
        flash("Terjadi kesalahan saat memproses file.")
        return redirect(url_for("home"))

    finally:
        input_path.unlink(missing_ok=True)



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

