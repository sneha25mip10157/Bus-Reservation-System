import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Choose sqlite by default. To use MySQL, set DB_TYPE='mysql' and provide MYSQL_USER/PASS/DB/HOST
DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')  # 'sqlite' or 'mysql'

if DB_TYPE == 'mysql':
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASS = os.environ.get('MYSQL_PASS', '')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'busdb')
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASS}@{MYSQL_HOST}/{MYSQL_DB}"
else:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'bus_reservation.db')

SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-secret')
