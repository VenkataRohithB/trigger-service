import re

import psycopg2
from psycopg2 import sql, extras, IntegrityError, DataError, DatabaseError, OperationalError, ProgrammingError
from psycopg2.errors import ForeignKeyViolation
from constants import *
from datetime import datetime


def parse_pgresponse(data):
    if not data:
        return data

    def format_row(row):
        return {
            key: (value.strftime('%Y-%m-%d %H:%M:%S.%f') if isinstance(value, datetime) else value)
            for key, value in row.items()
        }

    if isinstance(data, list):
        return [format_row(row) for row in data]
    return [format_row(data)]


class DBManager:
    def __init__(self):
        self.connection = None
        self.ensure_connection()

    def ensure_connection(self):
        """Ensures the database connection is active."""
        if self.connection is None or self.connection.closed:
            try:
                print(PG_PORT,PG_USER,PG_DATABASE,PG_HOST)
                self.connection = psycopg2.connect(
                    host=PG_HOST, dbname=PG_DATABASE, user=PG_USER, password=PG_PASSWORD, port=PG_PORT
                )
                self.connection.autocommit = True
                print("Database connection established successfully.")
            except Exception as e:
                raise Exception(f"Failed to connect to the database: {e}")


    def create_table(self, table_name: str) -> bool:
        query = sql.SQL("""CREATE TABLE IF NOT EXISTS {table}
         (
         id SERIAL PRIMARY KEY,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
         )
         """).format(table=sql.Identifier(table_name))
        if self.execute_query(query=query, insert=False):
            print(f"Table: [{table_name}] Created Successfully")
            return True
        print(f"create_table: [{table_name}] Something Went Wrong")
        return False

    def add_field(self, table_name: str, field_name: str, field_type: str, constraints: str = None) -> bool:
        field_definition = sql.SQL("{type}").format(type=sql.SQL(field_type))

        if constraints:
            field_definition += sql.SQL(" ") + sql.SQL(constraints)

        query = sql.SQL("ALTER TABLE {table} ADD COLUMN {field} {definition}").format(
            table=sql.Identifier(table_name),
            field=sql.Identifier(field_name),
            definition=field_definition)
        response = self.execute_query(query=query, insert=False)
        if response["status_bool"]:
            print(f"Field: [{field_name}] added to Table: [{table_name}]")
            return True
        print(f"Error in Adding Field: [{response}]")
        return False

    def add_foreign_key(self, table_name: str, field_name: str, ref_table: str, ref_field: str) -> bool:
        query = sql.SQL(
            "ALTER TABLE {table} ADD CONSTRAINT {constraint_name} FOREIGN KEY ({field}) REFERENCES {ref_table}({ref_field})")
        query = query.format(table=sql.Identifier(table_name),
                             constraint_name=sql.Identifier(f"{table_name}_{field_name}_fk"),
                             field=sql.Identifier(field_name),
                             ref_table=sql.Identifier(ref_table),
                             ref_field=sql.Identifier(ref_field))

        response = self.execute_query(query=query, insert=False)
        if response["status_bool"]:
            print(f"Foreign key constraint added to {field_name} in {table_name}, referencing {ref_table}({ref_field})")
            return True
        print(f"Error in Adding Foreign key: [{response}]")
        return False

    def drop_table(self, table_name: str) -> bool:
        query = sql.SQL("DROP TABLE IF EXISTS {table} CASCADE").format(table=sql.Identifier(table_name))
        response = self.execute_query(query=query, insert=False)
        if response["status_bool"]:
            print(f"Table: [{table_name}] is Deleted")
            return True
        print(f"Error in Deleting Table: [{response}]")
        return False

    def drop_view(self, view_name: str) -> bool:
        query = sql.SQL("DROP VIEW IF EXISTS {view} CASCADE").format(view=sql.Identifier(view_name))
        response = self.execute_query(query=query, insert=False)
        if response["status_bool"]:
            print(f"View: [{view_name}] is Deleted")
            return True
        print(f"Error in Deleting view: [{response}]")
        return False

    def select_query(self, table_name: str, get_items: list = None, condition_dict: dict = None,
                     num_records: int = None):
        # Base Query Build
        if get_items:
            columns = sql.SQL(", ").join(sql.Identifier(col) for col in get_items)
        else:
            columns = sql.SQL("*")
        query = sql.SQL("SELECT {columns} from {table}").format(columns=columns, table=sql.Identifier(table_name))

        # Adding condition (All AND)
        if condition_dict:
            conditions = sql.SQL(" WHERE ")
            conditions += sql.SQL(" AND ").join(
                sql.Composed([sql.Identifier(key), sql.SQL(" = "), sql.Placeholder(key)]) for key in condition_dict)
            query = query + conditions

        # Adding num_records
        if num_records:
            query += sql.SQL(" LIMIT {limit}").format(limit=sql.Literal(num_records))

        records = self.fetch_all(query=query, params=condition_dict)
        return parse_pgresponse(records)

    def insert_data(self, table_name: str, data: dict):
        fields = sql.SQL(", ").join(sql.Identifier(field) for field in data)
        values = sql.SQL(", ").join(sql.Placeholder(field) for field in data)
        query = sql.SQL("INSERT INTO {table} ({fields}) VALUES ({values}) RETURNING *").format(
            table=sql.Identifier(table_name),
            fields=fields, values=values)
        records = self.execute_query(query=query, params=data)
        return records

    def update_data(self, table_name: str, conditions: dict, data: dict):
        data["updated_at"] = datetime.now()

        update_query = sql.SQL(", ").join(
            sql.Composed([sql.Identifier(key), sql.SQL(" = "), sql.Placeholder(key)]) for key in data
        )

        condition_query = sql.SQL(" AND ").join(
            sql.Composed([sql.Identifier(key), sql.SQL(" = "), sql.Placeholder(f"cond_{key}")]) for key in conditions
        )

        params = {**data, **{f"cond_{key}": value for key, value in conditions.items()}}

        query = sql.SQL("UPDATE {table} SET {update_query} WHERE {condition_query} RETURNING *").format(
            table=sql.Identifier(table_name),
            update_query=update_query,
            condition_query=condition_query
        )

        records = self.execute_query(query=query, params=params)
        return parse_pgresponse(records)

    def delete_data(self, table_name: str, record_id: int = None, conditions: dict = None):
        if record_id is not None:
            query = sql.SQL("DELETE FROM {table} WHERE id = {id} RETURNING *").format(
                table=sql.Identifier(table_name),
                id=sql.Placeholder("id")
            )
            params = {"id": record_id}

        elif conditions:
            condition_statements = [sql.SQL("{col} = {val}").format(
                col=sql.Identifier(key),
                val=sql.Placeholder(key)
            ) for key in conditions.keys()]

            condition_clause = sql.SQL(" AND ").join(condition_statements)
            query = sql.SQL("DELETE FROM {table} WHERE {conditions} RETURNING *").format(
                table=sql.Identifier(table_name),
                conditions=condition_clause
            )
            params = conditions

        else:
            raise ValueError("Either 'record_id' or 'conditions' must be provided for deletion.")

        records = self.execute_query(query=query, params=params)
        return parse_pgresponse(data=records)

    def execute_query(self, query, params=None, insert=True):
        self.ensure_connection()
        try:
            with self.connection.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                self.connection.commit()

                if insert:
                    inserted_record = cursor.fetchone()
                    return {
                        "status_bool": True,
                        "records": parse_pgresponse(inserted_record),
                        "message": "Query executed successfully"
                    }

                return {
                    "status_bool": True,
                    "records": None,
                    "message": "Query executed successfully"
                }
        except ForeignKeyViolation as e:
            self.connection.rollback()
            return {"status_bool": False, "message": "Foreign key constraint failed: " + str(e)}

        except (IntegrityError, DataError, DatabaseError, OperationalError, ProgrammingError) as e:
            self.connection.rollback()
            return {"status_bool": False, "message": str(e)}
        except Exception as e:
            self.connection.rollback()
            return {"status_bool": False, "message": f"Unexpected error: {str(e)}"}

    def fetch_all(self, query, params=None, error_msg=None):
        try:
            with self.connection.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self.connection.rollback()
            print(f"{error_msg} - [{e}]")
            return None
