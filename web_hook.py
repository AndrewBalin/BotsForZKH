from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration

viber = Api(BotConfiguration(
    name='Jabka Bot',
    avatar='https://serg.zvezda72.ru/Viber/Jaba.png',
    auth_token='4eb6534fe2a7dc0a-ed6c0e4dd046f-fd402ef62acaf80b'
))

viber.set_webhook('https://serg.zvezda72.ru/viber_bot/')