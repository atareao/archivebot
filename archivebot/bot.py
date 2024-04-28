#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2023 Lorenzo Carbonell <a.k.a. atareao>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from io import StringIO
import json
import logging
import log
import os
from telegram import TelegramClient
from register import Register
from datetime import datetime
from context import Context
from iauploader import IAUploader
from converter import Converter


logger = logging.getLogger(__name__)

CURDIR = os.path.realpath(os.path.dirname(__file__))
CONFIG = os.path.join(CURDIR, "config.json")
MAXDATE = datetime(2023, 12, 2, 23, 59, 59)
HAND = "👉"
OK = "👍"
KO = "👎"


class BotException(Exception):
    pass


class Bot:
    @log.debug
    def __init__(self, token, chat_id, thread_id, ia_access: str,
                 ia_secret: str, podcast: str, creator: str,
                 register: Register, pool_time=300):
        self._pool_time = pool_time
        self._telegram_client = TelegramClient(token)
        self._token = token
        self._chat_id = int(chat_id)
        self._thread_id = int(thread_id)
        self._iauploader = IAUploader(token, ia_access, ia_secret, podcast,
                                      creator)
        self._register = register
        self._context = Context()
        self._read_config()

    @log.debug
    def _read_config(self) -> None:
        if os.path.exists(CONFIG):
            with open(CONFIG, "r") as fr:
                config = json.load(fr)
                self._offset = config["offset"]
        else:
            self._offset = 0

    @log.debug
    def _save_config(self) -> None:
        with open(CONFIG, "w") as fw:
            config = {
                "offset": self._offset
            }
            json.dump(config, fw)

    @log.debug
    def get_updates(self):
        response = self._telegram_client.get_updates(self._offset,
                                                     self._pool_time)
        if response["ok"] and response["result"]:
            offset = max([item["update_id"] for item in response["result"]])
            self._offset = offset + 1
            self._save_config()
            self._process_response(response)

    @log.debug
    def process_voice(self, message):
        logger.debug(f"Message: {message}")
        voice = message["message"]["voice"]
        audio = self._register.new(voice)
        logger.debug("===========================")
        logger.debug(type(audio))
        logger.debug(audio)
        logger.debug("===========================")
        file_id = audio.file_id
        file_info = self._telegram_client.get_file_info(file_id)
        logger.debug(file_info)
        audio = self._register.set_file_path(file_id, file_info["file_path"])
        logger.debug(audio)
        self._context.step = 1
        self._context.audio = audio
        message = ("A continuación, te preguntaré primero por el título,"
                   " luego por la descripción, y por último por las"
                   " etiquetas. En cada paso te preguntaré si quieres"
                   " continuar o modificar")
        self._telegram_client.send_message(message,
                                           self._chat_id,
                                           self._thread_id)
        self._telegram_client.send_message("Dime el título", self._chat_id,
                                           self._thread_id)

    @log.debug
    def process_callback_query(self, message):
        logger.debug(f"Message: {message}")
        data = message["callback_query"]["data"]
        if self._context.step == 2:
            if data == "Continuar":
                message = "Dime la descripción"
            else:
                self._context.step = 1
                message = "Dime el título"
            self._telegram_client.send_message(
                message, self._chat_id, self._thread_id)
        elif self._context.step == 3:
            if data == "Continuar":
                message = "Dime las etiquetas separadas por comas"
            else:
                message = "Dime la descripción"
                self._context.step = 2
            self._telegram_client.send_message(
                message, self._chat_id, self._thread_id)
        elif self._context.step == 4:
            if data == "Continuar":
                message = ("El audio queda así:\n"
                           f"Título: {self._context.audio.title}\n"
                           f"Descripción: {self._context.audio.description}\n"
                           f"Etiquetas: {self._context.audio.tags}")
                self._context.step = 5
                self._telegram_client.send_question(
                    message, self._chat_id,
                    ["Enviar", "Borrar"], self._thread_id)
            else:
                message = "Dime las etiquetas separadas por comas"
                self._context.step = 3
                self._telegram_client.send_message(
                    message, self._chat_id, self._thread_id)
        elif self._context.step == 5:
            if data == "Enviar":
                self.upload_audio()
            else:
                self.delete_audio()

    @log.debug
    def process_text(self, message):
        logger.debug(f"Message: {message}")
        text = message["message"]["text"]
        logger.debug(f"Text: {text}")
        if self._context.step == 1:
            audio = self._register.set_title(self._context.audio.identifier,
                                             text)
            self._context.audio = audio
            self._context.step = 2
            message_id = message["message"]["message_id"]
            self._telegram_client.set_reaction(self._chat_id, message_id, OK)
            self._telegram_client.send_question(
                f"Título: {text}", self._chat_id,
                ["Continuar", "Modificar"], self._thread_id)
        elif self._context.step == 2:
            audio = self._register.set_description(
                self._context.audio.identifier, text)
            self._context.audio = audio
            self._context.step = 3
            message_id = message["message"]["message_id"]
            self._telegram_client.set_reaction(self._chat_id, message_id, OK)
            self._telegram_client.send_question(
                f"Descripción: {text}", self._chat_id,
                ["Continuar", "Modificar"], self._thread_id)
        elif self._context.step == 3:
            tags = ",".join([tag.strip() for tag in text.split(",")])
            audio = self._register.set_tags(
                self._context.audio.identifier, tags)
            self._context.audio = audio
            self._context.step = 4
            message_id = message["message"]["message_id"]
            self._telegram_client.set_reaction(self._chat_id, message_id, OK)
            self._telegram_client.send_question(
                f"Etiquetas: {text}", self._chat_id,
                ["Continuar", "Modificar"], self._thread_id)
        elif self._context.step == 4:
            pass

        if text.startswith("/help") or text.startswith("/ayuda"):
            self.process_help(message)
        elif text.startswith("/"):
            command = text.split(" ")[0]
            msg = f"The command {command} is not implemented"
            raise BotException(msg)

    @log.debug
    def _process_response(self, response):
        chat_id = None
        thread_id = 0
        for index, message in enumerate(response["result"]):
            logger.debug(f"Number: {index}. Message: {message}")
            try:
                if "message" in message:
                    logger.debug("Es una respuesta message")
                    chat_id = message["message"]["chat"]["id"]
                    thread_id = message["message"]["message_thread_id"] if \
                        "message_thread_id" in message["message"] else 0
                    if chat_id != self._chat_id or \
                            thread_id != self._thread_id:
                        logger.debug(f"{chat_id} <=> {self._chat_id}")
                        logger.debug(f"{thread_id} <=> {self._thread_id}")
                        logger.debug("Me salgo")
                        return
                    if "voice" in message["message"]:
                        logger.debug("Es un mensaje de voz")
                        self.process_voice(message)
                    elif "text" in message["message"]:
                        logger.debug("Es un mensaje de texto")
                        self.process_text(message)
                    else:
                        logger.debug("No es nada?")
                elif "callback_query" in message:
                    logger.debug("Es una respuesta callback")
                    chat_id = \
                        message["callback_query"]["message"]["chat"]["id"]
                    if chat_id != self._chat_id:
                        logger.debug(f"{chat_id} <=> {self._chat_id}")
                        logger.debug("Me salgo")
                        return
                    self.process_callback_query(message)
                else:
                    logger.debug("No es nada?")
            except Exception as exception:
                if chat_id:
                    logger.error(exception)
                    self._telegram_client.send_message(str(exception), chat_id,
                                                       thread_id)

    @log.debug
    def process_help(self, message):
        chat_id = message["message"]["chat"]["id"]
        thread_id = message["message"]["message_thread_id"] if \
            "message_thread_id" in message["message"] else 0
        strbuf = StringIO()
        strbuf.write(f"`/ayuda` {HAND} muestra esta ayuda\n")
        self._telegram_client.send_message(strbuf.getvalue(), chat_id,
                                           thread_id)

    @log.debug
    def delete_audio(self):
        audio = self._context.audio
        file_path = audio.file_path.split("/")
        filename = f"/data/{self._token}/voice/{file_path[-1]}"
        logger.debug(filename)
        os.remove(filename)
        self._telegram_client.send_message("Archivo borrado",
                                           self._chat_id,
                                           self._thread_id)
        self._register.delete(audio.identifier)
        self._telegram_client.send_message("Audio borrado",
                                           self._chat_id,
                                           self._thread_id)

    @log.debug
    def upload_audio(self):
        audio = self._context.audio
        file_path = audio.file_path.split("/")
        filename = f"/data/{self._token}/voice/{file_path[-1]}"
        logger.debug(filename)
        outputfile = f"{os.path.splitext(filename)[0]}.mp3"
        logger.debug(outputfile)
        Converter.convert(filename, outputfile)
        self._telegram_client.send_message("Convertido a mp3",
                                           self._chat_id,
                                           self._thread_id)
        self._telegram_client.send_chat_action(self._chat_id, self._thread_id,
                                               "upload_voice")
        self._iauploader.upload(audio, outputfile)
        self._telegram_client.send_message("Subido a Internet Archive!",
                                           self._chat_id,
                                           self._thread_id)
