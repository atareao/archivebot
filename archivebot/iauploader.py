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

import logging
import log
from datetime import datetime
from audio import Audio
from internetarchive import get_session

logger = logging.getLogger(__name__)


class IAUploader:

    @log.debug
    def __init__(self, token: str, ia_access: str, ia_secret: str,
                 podcast: str, creator: str):
        self._token = token
        self._podcast = podcast
        self._creator = creator
        self._ia_session = get_session(config={
            "s3": {"access": ia_access, "secret": ia_secret}
        })

    @log.debug
    def upload(self, audio: Audio):
        now = datetime.now()
        metadata = {
            "title": audio.title,
            "mediatype": "audio",
            "collection": "opensource_audio",
            "date": now.strftime("%Y-%m-%d"),
            "description": audio.description,
            "podcast": self._podcast,
            "subject": audio.tags.split(","),
            "creator": self._creator,
        }
        file_path = audio.file_path.split("/")
        filename = f"/data/{self._token}/voice/{file_path[-1]}"
        ia_episode = self._ia_session.get_item(audio.identifier)
        response = ia_episode.upload(filename, metadata=metadata, verbose=True)
        logger.debug(f"Response: {response}")
