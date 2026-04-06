import csv
import io
from typing import Annotated

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, Form, UploadFile

app = APIGatewayRestResolver(enable_validation=True)


@app.post("/upload-csv")
def upload_csv(
    file_data: Annotated[UploadFile, File(description="CSV file to parse")],  # (1)!
    separator: Annotated[str, Form(description="CSV separator")] = ",",  # (2)!
):
    text = file_data.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text), delimiter=separator)
    rows = list(reader)

    return {
        "filename": file_data.filename,
        "total_rows": len(rows),
        "columns": list(rows[0].keys()) if rows else [],
        "data": rows,
    }


def lambda_handler(event, context):
    return app.resolve(event, context)
