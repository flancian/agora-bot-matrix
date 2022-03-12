from random import choice
from typing import List, Tuple
import urllib.parse
from maubot import Plugin, MessageEvent
from mautrix.types import RelationType, TextMessageEventContent, RelatesTo, MessageType
from mautrix import errors
from maubot.handlers import command
import datetime
import os
import re

AGORA_BOT_ID="anagora@matrix.org"
AGORA_URL=f"https://anagora.org"
MATRIX_URL=f"https://develop.element.io"
AGORA_ROOT=os.path.expanduser("~/agora")
OUTPUT_DIR=f"{AGORA_ROOT}/stream/{AGORA_BOT_ID}"
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
    
def log_evt(evt, node):

    try:
        os.mkdir(OUTPUT_DIR)
    except FileExistsError:
        pass

    # unsure if it's OK inlining, perhaps fine in this case as each room does explicit setup?
    msg = evt.content.body

    # this was shamelessly copy/pasted and adapted from [[agora bridge]], mastodon bot.
    if ('/' in node):
        # for now, dump only to the last path fragment -- this yields the right behaviour in e.g. [[go/cat-tournament]]
        node = os.path.split(node)[-1]

    filename = os.path.join(OUTPUT_DIR, node + '.md')
    print(f"logging {evt} to file {filename} mapping to {node}.")

    # hack hack -- this should be enabled/disabled/configured in the maubot admin interface somehow?
    try:
        with open(filename, 'a') as note:
            username = evt.sender
            # /1000 needed to reduce 13 -> 10 digits
            dt = datetime.datetime.fromtimestamp(int(evt.timestamp/1000))
            link = f'[link]({MATRIX_URL}/#/room/{evt.room_id}/{evt.event_id})'
            # note.write(f"- [[{username}]] at {dt}: {link}\n  - ```{msg}```")
            note.write(f"- [[{dt}]] [[{username}]] ({link}):\n  - {msg}\n")
    except Exception as e:
        print(f"Couldn't save link to message, exception: {e}.")


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
            response = f"\n".join(wikilinks)
            if inThread(evt):
                # already in a thread, can't start one :)
                await evt.reply(response, allow_html=True)
            else:
                # start a thread with our reply.
                content = TextMessageEventContent(
                        body=response, 
                        msgtype=MessageType.NOTICE,
                        relates_to=RelatesTo(rel_type=THREAD, event_id=evt.event_id))
                try:
                    await evt.respond(content, allow_html=True)  # Reply to user
                except errors.request.MUnknown: 
                    # works around: "cannot start threads from an event with a relation"
                    await evt.reply(response, allow_html=True)
