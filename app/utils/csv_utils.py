import csv
import io

from flask import Response


def rows_to_csv_response(filename, headers, rows):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    data = output.getvalue()
    output.close()
    return Response(
        data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def parse_csv_file(file_storage, required_columns):
    errors = []
    if not file_storage or not file_storage.filename:
        return [], ["No file uploaded."]

    content = file_storage.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return [], ["File must be UTF-8 encoded CSV."]

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return [], ["CSV file is empty or missing headers."]

    fieldnames = [f.strip() for f in reader.fieldnames]
    missing = [col for col in required_columns if col not in fieldnames]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return [], errors

    rows = []
    for row in reader:
        cleaned = {k.strip(): (v.strip() if v else "") for k, v in row.items() if k}
        if any(cleaned.values()):
            rows.append(cleaned)
    return rows, errors
