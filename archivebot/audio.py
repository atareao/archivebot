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

import logging
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Audio(BaseModel):
    id: int = -1
    identifier: str = ""
    title: str = ""
    description: str = ""
    tags: str = ""
    file_path: str = ""
    duration: int = 0
    mime_type: str = ""
    file_id: str = ""
    file_unique_id: str = ""
    file_size: int = 0
    published: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_cursor(cls, data: tuple):
        logger.debug("from_cursor")
        return cls(**{k: v for k, v in zip(cls.model_fields.keys(), data)})

    @classmethod
    def from_list(cls, data: list[tuple]):
        logger.debug("from_list")
        audios = []
        for item in data:
            audios.append(cls.from_cursor(item))
        return audios
