from random import choice
from typing import List, Tuple
import urllib.parse
from maubot import Plugin, MessageEvent
from mautrix.types import RelationType, TextMessageEventContent, RelatesTo, MessageType
from maubot.handlers import command
import re

THREAD = RelationType("io.element.thread")

def inThread(evt):
    try:
        content = evt.content
        relates = content._relates_to
        if relates.rel_type==THREAD:
            print(f"*** event was already in thread")
            return True
        return False
    except:
        return False
    

class AgoraPlugin(Plugin):
    @command.passive("\[\[(.+?)\]\]", multiple=True)
    async def handler(self, evt: MessageEvent, subs: List[Tuple[str, str]]) -> None:
        await evt.mark_read()
        print(f"responding to event: {evt}")
        response = ""
        wikilinks = []  # List of all wikilinks given by user
        for _, link in subs:
            if re.match('[0-9a-zA-Z -]+$', link):
                # prefer slugging simple links
                link = "https://anagora.org/{}".format(link.replace(' ', '-'))
            elif 'href=' in link or re.match('\[.+?\]\(.+?\)', link):
                # this wikilink is already anchored (resolved), skip it.
                continue
            else:
                # urlencode otherwise
                link = "https://anagora.org/{}".format(urllib.parse.quote(link))

            wikilinks.append(link)

        if wikilinks:
            wikilinks = f"\n".join(wikilinks)
            response += wikilinks
            if inThread(evt):
                # already in a thread, can't start one :)
                await evt.reply(response, allow_html=True)
            else:
                # start a thread with our reply.
                content = TextMessageEventContent(
                        body=response, 
                        msgtype=MessageType.NOTICE,
                        relates_to=RelatesTo(rel_type=THREAD, event_id=evt.event_id))
                await evt.respond(content, allow_html=True)  # Reply to user
