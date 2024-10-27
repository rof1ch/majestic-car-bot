import asyncio
from datetime import datetime
import log
import os
import yaml
import disnake
import disnake.types

from disnake.ext import commands
from dotenv import load_dotenv
from db import db


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SETTINGS_FILE = "config/settings.yaml"

logger = log.Logger()
orm = db.ORM()

error_embed = disnake.Embed(title="Ошибка", colour=0xFF0700)


def get_key_from_yaml(key):
    with open(SETTINGS_FILE) as f:
        set_file = yaml.safe_load(f)
        try:
            return set_file[key], None
        except:
            return None, f"Ошибка при получение данных из конфига по ключу - {key}"


MESSAGE_DELAY, err = get_key_from_yaml("message_delay")
if err != None:
    logger.log(3, err)
    MESSAGE_DELAY = 15


class SelectChannels(disnake.ui.ChannelSelect):
    def __init__(self, yaml_key):
        super().__init__(
            placeholder="Выберите канал",
            min_values=1,
            max_values=1,
            channel_types=[
                disnake.ChannelType.text,
            ],
        )
        self.yaml_key = yaml_key

    async def callback(self, inter: disnake.MessageInteraction):
        with open(SETTINGS_FILE) as f:
            set_file = yaml.safe_load(f)
        set_file[self.yaml_key] = inter.resolved_values[0].id
        with open(SETTINGS_FILE, "w") as f:
            yaml.dump(set_file, f)
        logger.log(2, f"{self.yaml_key} было выбрано - {inter.resolved_values[0].id}")
        await inter.response.send_message(
            f"Вы выбрали канал: {self.values[0]}",
            ephemeral=True,
            delete_after=MESSAGE_DELAY,
        )


class CarsDropdown(disnake.ui.StringSelect):
    def __init__(self):
        options = []
        cars, err = orm.get_list()
        if err != None:
            options.append(disnake.SelectOption(label=err))
        else:
            self.cars = cars
            for car in cars:
                options.append(disnake.SelectOption(value=car[0], label=car[1]))
        super().__init__(
            placeholder="Выберите автомобиль",
            max_values=1,
            min_values=1,
            options=options,
        )

    async def callback(self, inter: disnake.MessageInteraction):
        err = orm.remove_car(int(inter.values[0]))
        if err != None:
            error_embed.description = err
            await inter.response.send_message(
                embed=error_embed, ephemeral=True, delete_after=MESSAGE_DELAY
            )
        else:
            embed = disnake.Embed(title="Успешно удалена", color=disnake.Color.green())
            await inter.response.send_message(
                embed=embed, ephemeral=True, delete_after=MESSAGE_DELAY
            )


class InitApp(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectChannels("log_chanel"))
        db.init_db()


class AddCar(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Автомобиль",
                placeholder="Введите название автомобиля",
                custom_id="car_name",
                style=disnake.TextInputStyle.short,
            )
        ]
        super().__init__(title="Добавление автомобиля", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        mes = orm.add_car(inter.text_values["car_name"])
        if mes != None:
            error_embed.description = mes
            await inter.response.send_message(
                embed=error_embed, ephemeral=True, delete_after=MESSAGE_DELAY
            )
        else:
            embed = disnake.Embed(
                title="Добавление автомобиля",
                colour=0x4671D5,
                description=inter.text_values["car_name"],
            )

            await inter.response.send_message(
                embed=embed, ephemeral=True, delete_after=MESSAGE_DELAY
            )


class CloseBookingModal(disnake.ui.Modal):
    def __init__(self, booking_id, message_id):
        self.booking_id = booking_id
        self.message_id = message_id

        components = [
            disnake.ui.TextInput(
                label="Топливо",
                placeholder="Введите кол-во топлива",
                custom_id="end_fuel",
                style=disnake.TextInputStyle.short,
            )
        ]
        super().__init__(title="Сдача автомобиля", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        err = orm.close_booking(self.booking_id, inter.text_values["end_fuel"])
        if err != None:
            error_embed.description = err
            await inter.response.send_message(
                embed=error_embed, delete_after=MESSAGE_DELAY
            )
        else:
            if (
                2000 < int(inter.text_values["end_fuel"])
                or int(inter.text_values["end_fuel"]) <= 0
            ):
                error_embed.description = "Некорректное кол-во топлива"
                await inter.response.send_message(
                    embed=error_embed, ephemeral=True, delete_after=MESSAGE_DELAY
                )
            else:
                channel_id, err = get_key_from_yaml("log_chanel")
                if err != None:
                    error_embed.description = err
                    await inter.response.send_message(
                        embed=embed, ephemeral=True, delete_after=MESSAGE_DELAY
                    )
                else:
                    channel = client.get_channel(channel_id)
                    message = await channel.fetch_message(self.message_id)
                    old_embed = message.embeds[0]
                    old_embed.add_field(
                        "Окончательное топливо", inter.text_values["end_fuel"]
                    )
                    old_embed.add_field(
                        "Время сдачи", datetime.now().strftime("%Y-%m-%d %H:%M")
                    )
                    await message.edit(embed=old_embed)

                    embed = disnake.Embed(
                        title="Машина удачно сдана", color=disnake.Color.green()
                    )
                    await inter.response.send_message(
                        embed=embed, ephemeral=True, delete_after=MESSAGE_DELAY
                    )


class CloseBooking(disnake.ui.View):
    def __init__(self, booking_id, message_id):
        super().__init__(timeout=None)
        self.booking_id = booking_id
        self.message_id = message_id

    @disnake.ui.button(
        label="Сдать", style=disnake.ButtonStyle.red, custom_id=f"close_booking_"
    )
    async def close_booking(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        button.custom_id = f"close_booking_{self.booking_id}"
        await inter.response.send_modal(
            modal=CloseBookingModal(self.booking_id, self.message_id)
        )
        await inter.delete_original_message()


class GetCarModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="ID машины",
                placeholder="Введите ID машины",
                custom_id="car_id",
                style=disnake.TextInputStyle.short,
            ),
            disnake.ui.TextInput(
                label="Топливо",
                placeholder="Введите изначальное кол-во топлива",
                custom_id="start_fuel",
                style=disnake.TextInputStyle.short,
            ),
        ]
        super().__init__(title="Взять автомобиль", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        car, err = orm.get_car(inter.text_values["car_id"])
        if err != None:
            error_embed.description = err
            await inter.response.send_message(
                embed=error_embed, ephemeral=True, delete_after=MESSAGE_DELAY
            )
        elif len(car) == 0:
            error_embed.description = "Автомобиля с таким ID не существует"
            await inter.response.send_message(embed=error_embed, ephemeral=True)
        elif car[1] == 1:
            error_embed.description = "Данный автомобиль уже забронирован"
            await inter.response.send_message(
                embed=error_embed, ephemeral=True, delete_after=MESSAGE_DELAY
            )
        else:
            booking_id, err = orm.create_booking(
                inter.text_values["car_id"],
                inter.text_values["start_fuel"],
                inter.author.id,
            )
            if err != None:
                error_embed.description = err
                await inter.response.send_message(
                    embed=error_embed, ephemeral=True, delete_after=MESSAGE_DELAY
                )
            elif (
                2000 < int(inter.text_values["start_fuel"])
                or int(inter.text_values["start_fuel"]) <= 0
            ):
                error_embed.description = "Некорректное кол-во топлива"
                await inter.response.send_message(
                    embed=error_embed, ephemeral=True, delete_after=MESSAGE_DELAY
                )
            else:
                embed = disnake.Embed(title="Бронь машины", color=disnake.Color.blue())
                embed.add_field("Машина", car[0])
                embed.add_field("Начальное топливо", inter.text_values["start_fuel"])
                embed.set_author(
                    name=inter.author.name,
                    url=f"https://discordapp.com/users/{inter.author.id}",
                    icon_url=inter.author.avatar.url,
                )
                chanel_id, err = get_key_from_yaml("log_chanel")
                if err != None:
                    error_embed.description = err
                    await inter.response.send_message(
                        embed=error_embed, ephemeral=True, delete_after=15
                    )
                else:
                    log_chanel = client.get_channel(chanel_id)
                    message = await log_chanel.send(embed=embed)
                    embed.remove_author()
                    err = orm.update_message_id(
                        booking_id=booking_id, message_id=message.id
                    )
                    if err != None:
                        error_embed.description = err
                        await inter.response.send_message(
                            embed=error_embed,
                            ephemeral=True,
                            delete_after=MESSAGE_DELAY,
                        )
                    else:
                        view = CloseBooking(booking_id, message.id)
                        await inter.response.send_message(
                            embed=embed, ephemeral=True, view=view
                        )


class UserMenu(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="Взять машину", style=disnake.ButtonStyle.green)
    async def get_car(
        self, button: disnake.ui.button, inter: disnake.MessageInteraction
    ):
        await inter.response.send_modal(modal=GetCarModal())

    @disnake.ui.button(label="Список взятых машин", style=disnake.ButtonStyle.primary)
    async def list_cars(
        self, button: disnake.ui.button, inter: disnake.MessageInteraction
    ):
        booking_list, err = orm.get_user_bookings(inter.author.id)
        if err != None:
            error_embed.description = err
            await inter.response.send_message(
                embed=error_embed, ephemeral=True, delete_after=MESSAGE_DELAY
            )
        else:
            if len(booking_list) == 0:
                embed = disnake.Embed(title="Список пуст", color=disnake.Color.red())
                await inter.response.send_message(
                    embed=embed, ephemeral=True, delete_after=MESSAGE_DELAY
                )
            else:
                for booking in booking_list:
                    embed = disnake.Embed(
                        title="Бронь машины", color=disnake.Color.blue()
                    )
                    embed.add_field("Машина", booking[9])
                    embed.add_field("Начальное топливо", booking[3])
                    await inter.send(
                        embed=embed,
                        view=CloseBooking(booking[0], booking[6]),
                        ephemeral=True,
                    )


class GetListBookings(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)


class RemoveCar(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CarsDropdown())


class InitMainChannel(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectChannels("main_chanel"))


class StartBot(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(
        label="Выбрать машину",
        style=disnake.ButtonStyle.green,
        custom_id="start_bot_button",
    )
    async def get_car(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        view = UserMenu()
        embed = disnake.Embed(title="Список машин", colour=0xFB8500)
        cars, err = orm.get_list()
        if err != None:
            error_embed.description = err
            await inter.response.send_message(
                error_embed, ephemeral=True, delete_after=MESSAGE_DELAY
            )
        else:
            embed.description = ""
            for car in cars:
                embed.description += f"{car[0]} - {car[1]}\n"
            await inter.response.send_message(
                embed=embed, view=view, ephemeral=True, delete_after=MESSAGE_DELAY
            )


class AdminMenu(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=0)

    @disnake.ui.button(label="Зарегистрировать", style=disnake.ButtonStyle.blurple)
    async def init_app(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        view = InitApp()
        await inter.response.send_message(
            "Выберите канал для дальнейших логов",
            view=view,
            ephemeral=True,
            delete_after=MESSAGE_DELAY,
        )

    @disnake.ui.button(label="Добавить машину", style=disnake.ButtonStyle.green)
    async def add_car(
        self, button: disnake.ui.button, inter: disnake.MessageInteraction
    ):
        await inter.response.send_modal(modal=AddCar())

    @disnake.ui.button(label="Удалить машину", style=disnake.ButtonStyle.red)
    async def remove_car(
        self, button: disnake.ui.button, inter: disnake.MessageInteraction
    ):
        view = RemoveCar()
        await inter.response.send_message(
            view=view, ephemeral=True, delete_after=MESSAGE_DELAY
        )

    @disnake.ui.button(label="Выбрать основной канал", style=disnake.ButtonStyle.green)
    async def select_main_channel(
        self, button: disnake.ui.button, inter: disnake.MessageInteraction
    ):
        view = InitMainChannel()
        await inter.response.send_message(
            "Выберите основной канал бота",
            view=view,
            ephemeral=True,
            delete_after=MESSAGE_DELAY,
        )

    @disnake.ui.button(label="Запустить бота", style=disnake.ButtonStyle.green)
    async def start_bot(
        self, button: disnake.ui.button, inter: disnake.MessageInteraction
    ):
        chanel_id, err = get_key_from_yaml("main_chanel")
        if err != None:
            error_embed.description = err
            await inter.response.send_message(
                embed=error_embed, ephemeral=True, delete_after=MESSAGE_DELAY
            )
        else:
            chanel = client.get_channel(chanel_id)
            await chanel.purge(limit=100)
            embed = disnake.Embed(
                title="Автопарк",
                color=disnake.Color.green(),
                description="Здесь вы можете выбрать какую машину вы хотите взять. Каждая машина имеет свой ранг доступа. Не забывайте заправлять авто! Чтобы взять машину нажмите на кнопку внизу и заполните небольшую заявку. ",
            )
            await chanel.send(embed=embed, view=StartBot())
            embed = disnake.Embed(
                title="Бот успешно запущен", color=disnake.Color.green()
            )
            await inter.response.send_message(
                embed=embed, ephemeral=True, delete_after=MESSAGE_DELAY
            )

server_id, _ = get_key_from_yaml('server_id')
client = commands.Bot(
    command_prefix="!", intents=disnake.Intents.all(), test_guilds=[server_id]
)


@client.event
async def on_ready():
    client.add_view(StartBot())
    logger.log(2, f"We have logged in as {client.user}")


@client.slash_command(name="admin", description="Меню администратора")
@commands.has_permissions(administrator=True)
async def admin_menu(inter: disnake.ApplicationCommandInteraction):
    view = AdminMenu()
    embed = disnake.Embed(title="Меню администратора", colour=0x7C1F7C)
    await inter.response.send_message(view=view, embed=embed, ephemeral=True)


client.run(BOT_TOKEN)