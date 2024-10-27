from datetime import datetime
from typing import Optional
from mysql import connector
from mysql.connector.connection import MySQLConnection
from dataclasses import dataclass, fields
from typing import Any
from typing import TypeVar
from oslo_config import cfg

TypeofDataClass = TypeVar('TypeofDataClass', bound=dataclass())


class DatabaseAdapter(object):
    def __init__(self,
                 /) -> None:
        self.__host = cfg.CONF.database.host
        self.__username =  cfg.CONF.database.username
        self.__password =  cfg.CONF.database.password
        self.__auth_database =  cfg.CONF.database.database
        self.__connection = self.connect_database()

    def connect_database(self) -> Optional[MySQLConnection]:
        # noinspection PyBroadException
        try:
            self.__connection = connector.connect(
                host=self.__host,
                user=self.__username,
                password=self.__password,
                database=self.__auth_database
            )
            return self.__connection
        except connector.Error:
            return None

    def select_table(self,
                     table: str,
                     /,
                     *,
                     columns: str = "*",
                     where: Optional[str] = None,
                     limit: Optional[int] = None) -> list[dict[str, Any]]:

        self.query = f"SELECT {columns} FROM {table}"

        if where:
            self.query += f" WHERE {where}"

        if limit:
            self.query += f" LIMIT {limit}"

        return self.execute_query(self.query)

    def insert_data_in_table(self, table: str,
                             columns: list[str],
                             values: list[str],
                             /) -> str:
        columns_str = ', '.join(columns)
        values_str = ', '.join([f"'{value}'" for value in values])

        self.query = f"INSERT INTO {table} ({columns_str}) VALUES ({values_str})"
        return self.query

    def update_data_in_table(self,
                             table: str,
                             set_clause: str,
                             /,
                             *,
                             where: Optional[str] = None) -> str:

        cursor_ = self.__connection.cursor()
        self.query = f"UPDATE {table} SET {set_clause}"

        if where:
            self.query += f" WHERE {where}"

        cursor_.execute(self.query)
        return self.query

    def upsert_data_in_table(self,
                             table: str,
                             set_clause: str,
                             /):
        cursor_ = self.__connection.cursor()

        self.query = f"INSERT INTO {table} SET {set_clause} ON DUPLICATE KEY UPDATE {set_clause}"

        cursor_.execute(self.query)
        self.__connection.commit()
        return self.query


    def execute_query(self,
                      query: str,
                      /,
                      *,
                      commit_required: bool = False,
                      values_list: list = None) -> list[dict[str, Any]]:
        cursor_ = self.__connection.cursor()
        if values_list:
            cursor_.executemany(query, values_list)
        else:
            cursor_.execute(query)
        if commit_required:
            self.__connection.commit()
        result = cursor_.fetchall()
        if commit_required:
            return result

        column_names = [desc[0] for desc in cursor_.description]  # Get column names

        # Convert rows to list of dictionaries
        final_result = [dict(zip(column_names, row)) for row in result]
        return final_result

    def create_table_from_dataclass(self,
                                    dataclass_type: TypeofDataClass,
                                    table_name: str,
                                    /,
                                    *,
                                    primary_key: str = None):
        columns = []
        for field in fields(dataclass_type):
            column_name = field.name
            column_type = 'TEXT'
            if field.type == bool:
                column_type = 'Boolean'

            if field.type == int:
                column_type = 'Integer'

            if field.type == str:
                column_type = "VARCHAR(255)"

            if field.type == datetime:
                column_type = "DATETIME"

            if primary_key and column_name == primary_key:
                column_type += " PRIMARY KEY"

            columns.append(f"{column_name} {column_type}")

        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"

        self.execute_query(create_table_sql, commit_required=True)

    def update_table_with_dataclass_list(self,
                                         dataclass_list: TypeofDataClass,
                                         table_name: str
                                         ):
        if not dataclass_list:
            return

        columns = [field.name for field in fields(dataclass_list[0])]

        insert_into_data = f"""
                INSERT INTO {table_name} ({', '.join(columns)}) 
                VALUES ({', '.join(['%s'] * len(columns))}) 
                ON DUPLICATE KEY UPDATE 
                {', '.join([f"{column} = VALUES({column})" for column in columns])}
            """

        values_list = [
            tuple(getattr(data, column) for column in columns)
            for data in dataclass_list
        ]

        self.execute_query(insert_into_data, values_list=values_list, commit_required=True)


instance: Optional[DatabaseAdapter] = None
