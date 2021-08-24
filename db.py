import sqlite3
from sqlite3 import Error


class DBConnection:
    db_file_path = ''
    conn = None
    cursor = None

    def __init__(self):
        self.db_file_path = r"db/bot.db"

        sql_create_projects_table = """CREATE TABLE IF NOT EXISTS users (
                                        id integer PRIMARY KEY,
                                        name text NOT NULL,
                                        surname text,
                                        user_group text NOT NULL,
                                        room integer NOT NULL
                                    );"""

        sql_create_tasks_table = """CREATE TABLE IF NOT EXISTS default_answers (
                                        id integer PRIMARY KEY,
                                        key_words text NOT NULL,
                                        media_paths text,
                                        answer_text text NOT NULL
                                    );"""

        # create a database connection
        self.create_connection()

        # create tables
        if self.conn is not None:
            # create projects table
            self.create_table(sql_create_projects_table)

            # create tasks table
            self.create_table(sql_create_tasks_table)
        else:
            print("Error! cannot create the database connection.")

    def create_connection(self):
        """ create a database connection to the SQLite database
            specified by db_file_path
        :return: Connection object or None
        """
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.db_file_path)
            self.cursor = self.conn.cursor()
            return 0
        except Error as e:
            print(e)

        return 0

    def create_table(self, sql_query):
        """ create a table from the create_table_sql statement\
        :param sql_query: a CREATE TABLE statement
        :return:
        """
        try:
            self.cursor.execute(sql_query)
            self.conn.commit()
        except Error as e:
            print(e)

    def add_user(self, user_id: int, name: str, surname: str, group: str, room: int):
        self.cursor.execute('INSERT INTO users (id, name, surname, user_group, room) VALUES (?, ?, ?, ?, ?)',
                            (user_id, name, surname, group, room))
        self.conn.commit()

    def select_users(self, user_id: int = 0, room: int = 0, group: str = ''):
        if user_id:
            self.cursor.execute("SELECT * from users where id=?;", (user_id,))
            return self.cursor.fetchall()
        elif room:
            self.cursor.execute("SELECT * from users where room=?;", (room,))
            return self.cursor.fetchall()
        elif not group == '':
            self.cursor.execute("SELECT * from users where user_group=?;", (group,))
            return self.cursor.fetchall()
        else:
            self.cursor.execute("SELECT * from users;")
            return self.cursor.fetchall()


if __name__ == '__main__':
    db_connection = DBConnection()
    print(db_connection.select_users())
    print(db_connection.select_users(user_id=1012))
    print(db_connection.select_users(group='админ'))
