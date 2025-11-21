# emanager.py
import click
import database
from goals import goal
from log_event import log
from analysis import report, plan, journal, trend
from track import start, stop
from importer import import_data

@click.group()
def emanager():
    """A personal energy manager CLI."""
    pass

@emanager.command()
def init():
    """Initializes the database."""
    conn = database.create_connection()
    database.create_tables(conn)
    database.migrate_db(conn) # Apply migrations
    conn.close()
    click.echo("Database initialized and migrations applied.")

emanager.add_command(goal)
emanager.add_command(log)
emanager.add_command(report)
emanager.add_command(start)
emanager.add_command(stop)
emanager.add_command(plan)
emanager.add_command(import_data)
emanager.add_command(journal)
emanager.add_command(trend)


if __name__ == "__main__":
    emanager()