import sqlite3
from log import Logger
from datetime import datetime, timedelta, timezone


def init_db():
    connection = sqlite3.connect("db/database.db")
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Cars (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			car_name TEXT NOT NULL,
   			status BOOLEAN DEFAULT 0
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
			message_id TEXT,
			end_time TEXT,
   			FOREIGN KEY(car_id) REFERENCES Cars(id)
		)
  	"""
    )
    connection.commit()


class ORM:
    connection = sqlite3.connect("db/database.db")
    cursor = connection.cursor()
    logger = Logger()

    def add_car(self, car_name: str):
        try:
            self.cursor.execute("INSERT INTO Cars (car_name) VALUES (?)", (car_name,))
            self.logger.log(2, f"Успешно добавлен автомобиль - {car_name}")
            self.connection.commit()
            return None
        except sqlite3.Error as error:
            self.logger.log(
                4, f"Ошибка при добавление автомобиля - {car_name}. Ошибка: {error}"
            )
            return f"Ошибка при добавление автомобиля - {car_name}."

    def get_list(self):
        try:
            self.cursor.execute("SELECT * FROM Cars WHERE status = 0")
            records = self.cursor.fetchall()
            self.logger.log(2, "Список машин успешно получен")
            return records, None
        except sqlite3.Error as error:
            self.logger.log(4, f"Ошибка при получение автомобилей. Ошибка: {error}")
            return None, f"Ошибка при получение автомобилей."

    def remove_car(self, car_id):
        try:
            self.cursor.execute("DELETE FROM Cars WHERE id = (?)", (car_id,))
            self.connection.commit()
            return None
        except sqlite3.Error as error:
            self.logger.log(
                4, f"Ошибка при удаление автомобиля {car_id}. Ошибка: {error}"
            )
            return f"Ошибка при удаление автомобиля"

    def change_status_car(self, car_id, status):
        try:
            self.cursor.execute(
                "Update Cars SET status=? WHERE id = ?",
                (
                    status,
                    car_id,
                ),
            )
            self.connection.commit()
            return None
        except sqlite3.Error as error:
            self.logger.log(
                4, f"Ошибка при обновление статуса машины {car_id}. Ошибка: {error}"
            )
            return f"Ошибка при обновление статуса машины"

    def create_booking(self, car_id, start_fuel, user_id):
        try:
            self.cursor.execute(
                "INSERT INTO CarsUsers(user_id, car_id, start_fuel) VALUES (?, ?, ?)",
                (
                    user_id,
                    car_id,
                    start_fuel,
                ),
            )
            self.connection.commit()
            err = self.change_status_car(car_id=car_id, status=1)
            if err != None:
                return 0, err
            else:
                return self.cursor.lastrowid, None
        except sqlite3.Error as error:
            self.logger.log(
                4,
                f"Ошибка при создание брони, user_id={user_id}, car_id={car_id}. Ошибка: {error}",
            )
            return 0, f"Ошибка при создание брони"

    def update_message_id(self, booking_id, message_id):
        try:
            self.cursor.execute(
                "UPDATE CarsUsers SET message_id=(?) WHERE id = (?) ",
                (
                    message_id,
                    booking_id,
                ),
            )
            self.connection.commit()
            return None
        except sqlite3.Error as error:
            self.logger.log(
                4,
                f"Ошибка при добавление message_id({message_id}) к брони - {booking_id}. Ошибка: {error}",
            )
            return f"Ошибка при обновление брони"

    def get_car(self, car_id):
        try:
            self.cursor.execute(
                "SELECT car_name, status FROM Cars WHERE id = ?", (car_id,)
            )
            return self.cursor.fetchone(), None
        except sqlite3.Error as error:
            self.logger.log(
                4, f"Ошибка при получение машины - {car_id}. Ошибка: {error}"
            )
            return None, f"Ошибка при получение машины"

    def get_booking(self, booking_id):
        try:
            self.cursor.execute(
                "SELECT car_id FROM CarsUsers WHERE id = (?)", (booking_id,)
            )
            return self.cursor.fetchone(), None
        except sqlite3.Error as error:
            self.logger.log(
                4, f"Ошибка при получение брони - {booking_id}. Ошибка {error}"
            )
            return None, f"Ошибка при получение брони"

    def get_user_bookings(self, user_id):
        try:
            self.cursor.execute(
                "SELECT * FROM CarsUsers JOIN Cars ON Cars.id = CarsUsers.car_id WHERE CarsUsers.user_id = (?) AND CarsUsers.status = 0 ",
                (user_id,),
            )
            return self.cursor.fetchall(), None
        except sqlite3.Error as error:
            self.logger.log(
                4,
                f"Ошибка при получение брони пользователя - {user_id}. Ошибка {error}",
            )
            return None, f"Ошибка при получение брони пользователя"

    def close_booking(self, booking_id, end_fuel):
        try:
            tzinfo = timezone(timedelta(hours=3))
            self.cursor.execute(
                "UPDATE CarsUsers SET end_fuel=(?), status=1, end_time = (?) WHERE id = (?)",
                (
                    end_fuel,
                    datetime.now(tzinfo).strftime("%Y-%m-%d %H:%M"),
                    booking_id,
                ),
            )

            car_id, err = self.get_booking(booking_id)
            if err != None:
                return err

            err = self.change_status_car(car_id[0], 0)
            if err != None:
                return err
            return None
        except sqlite3.Error as error:
            self.logger.log(
                4, f"Ошибка при закрытие брони - {booking_id}.Ошибка: {error}"
            )
            return f"Ошибка при закрытие брони"
