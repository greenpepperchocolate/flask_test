from flask import Flask, request, jsonify, render_template
import pandas as pd

app = Flask(__name__)

MAX_PREVIEW_ROWS = 10


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
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
    app.run(debug=True)
