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

import log
import logging
import sqlite3
import uuid
from datetime import datetime
from audio import Audio


AUDIOS = """
    CREATE TABLE IF NOT EXISTS audios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifier TEXT NOT NULL,
        title TEXT DEFAULT "",
        description TEXT DEFAULT "",
        tags TEXT DEFAULT "",
        file_path TEXT DEFAULT "",
        duration INTEGER NOT NULL,
        mime_type TEXT NOT NULL,
        file_id TEXT NOT NULL,
        file_unique_id TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        published BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""

logger = logging.getLogger(__name__)


class RegisterException(Exception):
    pass


class RegisterExists(Exception):
    pass


class RegisterNotExists(Exception):
    pass


class Register:

    @log.debug
    def __init__(self, db):
        self._connection = sqlite3.connect(db)
        try:
            cursor = self._connection.cursor()
            cursor.execute(AUDIOS)
            self._connection.commit()
        except Exception as e:
            raise RegisterException(e)

    @log.debug
    def new(self, voice: dict) -> Audio:
        try:
            sql = ("INSERT INTO audios (identifier, duration, mime_type,"
                   " file_id, file_unique_id, file_size) VALUES (?, ?, ?, ?, "
                   "?, ?) RETURNING *")
            identifier = uuid.uuid4().hex
            data = (identifier, voice["duration"], voice["mime_type"],
                    voice["file_id"], voice["file_unique_id"],
                    voice["file_size"])
            cursor = self._connection.execute(sql, data)
            audio = Audio.from_cursor(cursor.fetchone())
            self._connection.commit()
            return audio
        except Exception as e:
            raise RegisterException(e)

    @log.debug
    def set_file_path(self, file_id: str, file_path: str) -> Audio:
        try:
            sql = ("UPDATE audios SET file_path = ?, updated_at = ?"
                   " WHERE file_id = ? RETURNING *")
            updated_at = datetime.now()
            data = (file_path, updated_at, file_id)
            cursor = self._connection.execute(sql, data)
            audio = Audio.from_cursor(cursor.fetchone())
            self._connection.commit()
            return audio
        except Exception as e:
            raise RegisterException(e)

    @log.debug
    def set_title(self, identifier: str, title: str) -> Audio:
        try:
            sql = ("UPDATE audios SET title = ?, updated_at = ?"
                   " WHERE identifier = ? RETURNING *")
            updated_at = datetime.now()
            data = (title, updated_at, identifier)
            cursor = self._connection.execute(sql, data)
            audio = Audio.from_cursor(cursor.fetchone())
            self._connection.commit()
            return audio
        except Exception as e:
            raise RegisterException(e)

    @log.debug
    def set_description(self, identifier: str, description: str) -> Audio:
        try:
            sql = ("UPDATE audios SET description = ?, updated_at = ?"
                   " WHERE identifier = ? RETURNING *")
            updated_at = datetime.now()
            data = (description, updated_at, identifier)
            cursor = self._connection.execute(sql, data)
            audio = Audio.from_cursor(cursor.fetchone())
            self._connection.commit()
            return audio
        except Exception as e:
            raise RegisterException(e)

    @log.debug
    def set_tags(self, identifier: str, tags: str) -> Audio:
        try:
            sql = ("UPDATE audios SET tags = ?, updated_at = ?"
                   " WHERE identifier = ? RETURNING *")
            updated_at = datetime.now()
            data = (tags, updated_at, identifier)
            cursor = self._connection.execute(sql, data)
            audio = Audio.from_cursor(cursor.fetchone())
            self._connection.commit()
            return audio
        except Exception as e:
            raise RegisterException(e)

    @log.debug
    def delete(self, identifier: str) -> Audio:
        try:
            sql = ("DELETE FROM audios WHERE identifier = ? RETURNING *")
            data = (identifier,)
            cursor = self._connection.execute(sql, data)
            audio = Audio.from_cursor(cursor.fetchone())
            self._connection.commit()
            return audio
        except Exception as e:
            raise RegisterException(e)

    @log.debug
    def get_unpublished(self) -> list[Audio]:
        try:
            sql = "SELECT * WHERE published = ?"
            data = (False,)
            cursor = self._connection.execute(sql, data)
            audios = Audio.from_list(cursor.fetchall())
            self._connection.commit()
            return audios
        except Exception as e:
            raise RegisterException(e)

    @log.debug
    def list(self) -> list[Audio]:
        try:
            sql = "SELECT * FROM audios"
            cursor = self._connection.execute(sql)
            audios = Audio.from_list(cursor.fetchall())
            self._connection.commit()
            return audios
        except Exception as e:
            raise RegisterException(e)

    @log.debug
    def count(self) -> int:
        try:
            sql = "SELECT count(1) FROM audios"
            cursor = self._connection.cursor()
            res = cursor.execute(sql)
            return res.fetchone()
        except Exception as e:
            raise RegisterException(e)
