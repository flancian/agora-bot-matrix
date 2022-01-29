from random import choice
from typing import List, Tuple
import urllib.parse
from maubot import Plugin, MessageEvent
from maubot.handlers import command


class AgoraPlugin(Plugin):
    @command.passive("\[\[(.+)\]\]", multiple=True)
    async def handler(self, evt: MessageEvent, subs: List[Tuple[str, str]]) -> None:
        await evt.mark_read()
        wikilinks = []  # List of all wikilinks given by user
        for _, link in subs:
            link = "https://anagora.org/{}".format(urllib.parse.quote(link))

            wikilinks.append(link)

        if wikilinks:
            wikilinks = f"\n".join(wikilinks)
            response = wikilinks
            await evt.reply(response, allow_html=True)  # Reply to user
