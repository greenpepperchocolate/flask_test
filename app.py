import os
from functools import wraps

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import pandas as pd
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
ALLOWED_EMAILS = {
    e.strip().lower()
    for e in os.environ.get("ALLOWED_EMAILS", "").split(",")
    if e.strip()
}

MAX_PREVIEW_ROWS = 10


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_email"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


@app.route("/login")
def login():
    if session.get("user_email"):
        return redirect(url_for("index"))
    return render_template("login.html", google_client_id=GOOGLE_CLIENT_ID)


@app.route("/auth/callback", methods=["POST"])
def auth_callback():
    token = request.form.get("credential")
    if not token:
        return "認証情報がありません", 400

    try:
        info = google_id_token.verify_oauth2_token(
            token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        return "認証に失敗しました", 401

    email = (info.get("email") or "").lower()
    if not info.get("email_verified") or email not in ALLOWED_EMAILS:
        return "このアカウントにはアクセス権がありません", 403

    session["user_email"] = email
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return render_template("index.html", user_email=session.get("user_email"))


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "ファイルが選択されていません"}), 400

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "CSVファイルを選択してください"}), 400

    try:
        df = pd.read_csv(file)
    except Exception as e:
        return jsonify({"error": f"CSVの読み込みに失敗しました: {e}"}), 400

    if df.empty:
        return jsonify({"error": "CSVにデータがありません"}), 400

    original_rows, original_cols = df.shape
    missing_counts = df.isnull().sum()
    duplicate_count = int(df.duplicated().sum())

    # 加工: 重複行を除去
    df_cleaned = df.drop_duplicates()

    numeric_df = df_cleaned.select_dtypes(include="number")
    if not numeric_df.empty:
        describe_html = numeric_df.describe().round(2).to_html(classes="table", border=0)
    else:
        describe_html = "<p class='muted'>数値列がありません</p>"

    columns_info = [
        {
            "column": str(col),
            "dtype": str(dtype),
            "missing": int(missing_counts[col]),
        }
        for col, dtype in df.dtypes.items()
    ]

    preview_html = df_cleaned.head(MAX_PREVIEW_ROWS).to_html(
        classes="table", border=0, index=False
    )

    result = {
        "filename": file.filename,
        "original_rows": original_rows,
        "original_cols": original_cols,
        "duplicate_removed": duplicate_count,
        "rows_after_cleaning": df_cleaned.shape[0],
        "columns_info": columns_info,
        "describe_html": describe_html,
        "preview_html": preview_html,
    }
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)
