from datetime import datetime
import typer


def format_entries_for_table(entries) -> list[tuple[str, str, str, str]]:
    formatted_rows: list[tuple[str, str, str, str]] = []
    for entry in entries:
        try:
            start_dt = datetime.fromisoformat(entry["start_datetime"])
            start_display = start_dt.strftime("%H:%M")
        except ValueError:
            start_display = entry["start_datetime"]

        minutes = entry["tracked_minutes"]
        minutes_display = "RUNNING" if minutes == 0 else str(minutes)
        description = entry["description"] or ""
        formatted_rows.append(
            (str(entry["id"]), start_display, minutes_display, description)
        )
    return formatted_rows


def render_table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> None:
    if not rows:
        return

    column_widths = [
        max(len(headers[index]), max(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]

    header_line = " | ".join(
        headers[index].ljust(column_widths[index]) for index in range(len(headers))
    )
    separator = "-+-".join("-" * column_widths[index] for index in range(len(headers)))

    typer.echo(header_line)
    typer.echo(separator)
    for row in rows:
        typer.echo(
            " | ".join(
                row[index].ljust(column_widths[index]) for index in range(len(headers))
            )
        )
