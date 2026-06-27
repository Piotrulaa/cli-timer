from datetime import date, datetime

import typer
from .db import DatabaseConnector
from .utils import format_entries_for_table, render_table

state = {
    "status_requested": False,
}


def get_db() -> DatabaseConnector:
    """
    Initialize the database and create the example table if it doesn't exist
    """
    db_connector = DatabaseConnector()
    db_connector.create_example_table()
    return db_connector


db_connector = get_db()


def result_callback(command_result, **kwargs):
    """
    Function called after each command
    """

    # After status was printed, reset status request state
    if state["status_requested"]:
        entries = db_connector.get_entries_by_date(date.today())
        if not entries:
            typer.echo("No time tracked today.")
            typer.echo("There is no tracking currently running.")
            typer.echo("Use 'start' command to begin tracking time.")
        else:
            total_minutes = sum(entry["tracked_minutes"] for entry in entries)
            typer.echo(f"Total time tracked today: {total_minutes} minutes")
            if entries[-1]["tracked_minutes"] == 0:
                typer.echo("There is currently a tracking session running.")
            else:
                typer.echo("There is no tracking currently running.")

        state["status_requested"] = False


app = typer.Typer(
    result_callback=result_callback, invoke_without_command=True, no_args_is_help=True
)


@app.callback()
def main(
    status: bool = typer.Option(False, "--status", "-s", help="Show tracking status")
):
    """
    Simple CLI timer application
    """
    if status:
        state["status_requested"] = True


@app.command()
def start(
    description: str = typer.Option(
        "", "--description", "-d", help="Description for the tracking session"
    )
):
    """
    Start time tracking
    """
    last_entry = db_connector.get_last_entry()
    if last_entry and last_entry["tracked_minutes"] == 0:
        typer.echo("A tracking session is already running.")
    else:
        db_connector.add_entry(start_datetime=datetime.now(), description=description)
        typer.echo("Time tracking started.")


@app.command()
def stop():
    """
    Stop time tracking
    """
    last_entry = db_connector.get_last_entry()
    if not last_entry or last_entry["tracked_minutes"] > 0:
        typer.echo("No tracking session is currently running.")
    else:
        start_time = datetime.fromisoformat(last_entry["start_datetime"])
        tracked_minutes = round((datetime.now() - start_time).total_seconds() / 60)
        updated = db_connector.update_entry(
            entry_id=last_entry["id"],
            start_datetime=start_time,
            tracked_minutes=tracked_minutes,
            description=last_entry["description"],
        )
        if not updated:
            typer.echo("Could not stop tracking session due to a database update error.")
            return
        typer.echo(
            f"Time tracking stopped. Total time tracked: {tracked_minutes} minutes."
        )


@app.command("today")
def today_entries():
    """
    Show all entries from today in a table.
    """
    entries = db_connector.get_entries_by_date(date.today())
    if not entries:
        typer.echo("No entries for today.")
        return

    headers = ("ID", "Start", "Minutes", "Description")
    rows = format_entries_for_table(entries)
    render_table(headers, rows)


@app.command()
def cancel():
    """
    Cancel currently running tracking session by deleting the latest entry.
    """
    last_entry = db_connector.get_last_entry()
    if not last_entry:
        typer.echo("No entries found.")
        return

    if last_entry["tracked_minutes"] != 0:
        typer.echo("Latest entry is already finished and cannot be canceled.")
        return

    deleted = db_connector.delete_entry(last_entry["id"])
    if deleted:
        typer.echo("Latest running entry canceled.")
    else:
        typer.echo("Could not cancel the latest entry.")
