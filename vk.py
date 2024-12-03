from vkbottle.bot import Bot, Message

from utils import Days, BotType
from cntnt import *

class VK_Sender:
    @property
    def db_type(self):
        return self.db_type

    def __init__(self, token, db_handler, ms_producer, logger):
        self._db_type = BotType.VK.value
        self._bot = Bot(token=token)
        self._db_handler = db_handler
        self._ms_producer = ms_producer
        self._logger = logger
        self._user_inreract = {}

        @self._bot.on.message(text=f'/{CMD_HELP}')
        async def help_send(message):
            """
            Подсказка - вывод доступных команд
            """
            await message.answer(message.chat.id, Help)

        # @self._bot.on.private_message(text=f'/{CMD_STAT}')
        # async def stat_send(message):
        #     """
        #     Статистика по боту
        #     """
        #     text = Unknown
        #     # и только если пользователь существует и администратор
        #     if user := await self._db_handler.get_user_info(message.chat.id, self._db_type):
        #         if user['admin'] == True:
        #             all_users = await self._db_handler.get_users(self._db_type)
        #             p_count, g_count = [0,0], [0,0]
        #             for u in all_users:
        #                 if u['id'] > 0: counter = p_count
        #                 else:           counter = g_count
        #                 counter[0] += 1
        #                 if u['mailing']:
        #                     counter[1] += 1
        #             text = Statistic.format(p_count[0], p_count[1], g_count[0], g_count[1])
        #     await message.reply(message, text)

        @self._bot.on.message()
        async def all_get(message):
            print('GET', message)

        # @self._bot.on.private_message(text="/callback")
        # async def send_callback_button(message: Message):
        #     await message.answer("Лови!")

    def poll(self):
        """
        Вернуть асинхронную функцию бесконечного опроса бота
        """
        return self._bot.run_polling()
        # raise RuntimeError('Not supported. Use run() function.')

    def run(self):
        """
        Вернуть обычную функцию бесконечного опроса бота
        """
        self._bot.run_forever()
