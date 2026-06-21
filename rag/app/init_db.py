from pathlib import Path
from .db import get_conn


def main():
    sql_path = Path(__file__).resolve().parents[2] / 'infra' / 'sql' / '001_init.sql'
    sql = sql_path.read_text(encoding='utf-8')
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
    print('Database initialized')


if __name__ == '__main__':
    main()
