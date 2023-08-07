[![pytest](https://github.com/IRFM/thermal-events/actions/workflows/main.yml/badge.svg)](https://github.com/IRFM/thermal-events/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/IRFM/thermal-events/branch/new_database_structure/graph/badge.svg?token=3VRZQ9J5W5)](https://codecov.io/gh/IRFM/thermal-events)

Python library that handles the thermal events and the interaction with the thermal events database of fusion reactors.

A `.env` file must be created, containing the credentials to connect to the thermal events database.
The `.env` file must be located at the path from which python is run.

Example of .env file: 
```bash
# Hostname of the thermal events database
MYSQL_HOST = "host"
# Name of the database
MYSQL_DATABASE = "database"
# Username to connect to the host
MYSQL_USER = "user"
# Password to connect to the host
MYSQL_PASSWORD = "password"

# Set to True to use a SQLite database contained in a .db file located at the root folder of the project
SQLITE = False
# Name of the SQLite database file
SQLITE_DATABASE_FILE = "database.db"
```
