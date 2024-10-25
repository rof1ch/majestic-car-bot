import sqlite3

connection = sqlite3.connect("database.db")
cursor = connection.cursor()


connection.commit()


def init_db():
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Cars (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			car_name TEXT NOT NULL
	    )
    """
    )
    cursor.execute(
        """
		CREATE TABLE IF NOT EXISTS CarsUsers (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			user_id TEXT NOT NULL,
			car_id INTEGER NOT NULL,
			start_fuel INTEGER NOT NULL,
			end_fuel INTEGER DEFAULT 0,
			status BOOLEAN DEFAULT 0,
   			FOREIGN KEY(car_id) REFERENCES Cars(id)
		)
  	"""
    )
    connection.commit()


connection.close()
