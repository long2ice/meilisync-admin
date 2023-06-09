import datetime
import json

import typer
from cryptography.fernet import Fernet

app = typer.Typer()

ENCRYPT_KEY = b"AAFCOToFiXipuZIx0MDaUohmS3IVisALfmE_ylk9zRI="


@app.command()
def generate(
    end_date: str = typer.Option(
        None, "-e", "--end-date", help="License expire date, format: YYYY-MM-DD"
    ),
    end_days: int = typer.Option(None, "-d", "--end-days", help="License expire days"),
    name: str = typer.Option(..., "-n", "--name", help="License name"),
    machine_id: str = typer.Option(..., "-m", "--machine-id", help="Unique machine ID"),
):
    if not end_date and not end_days:
        raise typer.BadParameter("Must specify end_date or end_days")
    if end_days:
        end_date = (datetime.date.today() + datetime.timedelta(days=end_days)).strftime(
            "%Y-%m-%d"
        )
    license_file = "license.txt"
    with open(license_file, "w") as f:
        data = json.dumps({"expire": end_date, "name": name, "machine_id": machine_id})
        fernet = Fernet(ENCRYPT_KEY)
        f.write(fernet.encrypt(data.encode()).decode())


if __name__ == "__main__":
    app()
