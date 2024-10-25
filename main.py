import log
import os
import yaml
import disnake
import disnake.types
from typing import Optional
from disnake.ext import commands
from disnake import ChannelType
from dotenv import load_dotenv


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SETTINGS_FILE = "settings.yaml"


logger = log.Logger()


class SelectChannels(disnake.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="Выберите канал",
            min_values=1,
            max_values=1,
        )

    async def callback(self, inter: disnake.MessageInteraction):
        with open(SETTINGS_FILE) as f:
            set_file = yaml.safe_load(f)
        set_file["log_chanel"] = inter.resolved_values[0].id
        with open(SETTINGS_FILE, "w") as f:
            yaml.dump(set_file, f)
        logger.log(2, f"Основным каналом было выбрано - {inter.resolved_values[0].id}")
        await inter.response.send_message(f"Вы выбрали канал: {self.values[0]}")


class IsnitApp(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectChannels())
        

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
        
        embed = disnake.Embed(title="Добавление автомобиля")
        embed.add_field(
            name="Наименование автомобиля",
            value=inter.text_values["car_name"],
            inline=False,
        )
        logger.log(2, f"Добавление автомобиля - {inter.text_values['car_name']}")
        await inter.response.send_message(embed=embed, ephemeral=True)

class GetCar(disnake.ui.Modal):
    

class Menu(disnake.ui.View):
    
    def __init__(self):
        super().__init__(timeout=None)
        self.value = Optional[bool]
        
    @disnake.ui.button(label='Взять машину', style=disnake.ButtonStyle.blurple)
    async def get_car(self, button:disnake.ui.button, inter: disnake.MessageInteraction):
        await inter.response.send_modal(modal=)

client = commands.Bot(command_prefix="!", intents=disnake.Intents.all())


@client.event
async def on_ready():
    logger.log(2, f"We have logged in as {client.user}")


@client.slash_command(name="init", description="Выбор канала для сохранения логов")
@commands.has_permissions(administrator=True)
async def init_app(inter: disnake.ApplicationCommandInteraction):
    view = InitApp()
    await inter.response.send_message(
        "Выберите канал для дальнейших логов", view=view, ephemeral=True
    )


@client.slash_command(name="add")
@commands.has_permissions(administrator=True)
async def add_car(inter: disnake.AppCmdInter):
    await inter.response.send_modal(modal=AddCar())


client.run(BOT_TOKEN)
