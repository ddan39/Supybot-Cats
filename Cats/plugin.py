###
# Copyright (c) 2014, Miyrah, Dan39
# All rights reserved.
#
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Cats')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

import time
import random
import os.path
import supybot.ircmsgs as ircmsgs
import supybot.schedule as schedule


class Cats(callbacks.Plugin):
    """Add the help for "@plugin help Cats" here
    This should describe *how* to use this plugin."""

    def __init__(self, irc):
        self.__parent = super(Cats, self)
        self.__parent.__init__(irc)

        self.gamechan = '#games'

        self.catsrunning = False
        self.catsjoining = False
        self.catsplaying = False
        self.players = {}

        gamecards = open(os.path.join(os.path.dirname(__file__), 'lists')) .read()
        self.gamecards = gamecards.split('=^-^=')

    def cats(self, irc, msg, args):
        """docstring"""
        if msg.args[0] == self.gamechan:
            if self.catsrunning:
                irc.error('The cats are already running!')
            else:
                irc.reply('Starting Scattergories...\x02type !jcats to join\x02. Categories will be revealed in 30 seconds, then a letter will be chosen.', prefixNick=False)
                irc.reply('Players will have 60 seconds to PM answers matching the categories starting with that letter to IPT.', prefixNick=False)
                irc.reply('For example, letter A, category 4, Math Terms, you could PM 4 addition. At the end of the round, you will receive points for unique answers.', prefixNick=False)
                self.catsrunning = True
                self.catsjoining = True

                def listCats():
                    self.catsjoining = False
                    irc.reply('Users in this round: %s' % ', '.join(self.players.keys()), prefixNick=False)
                    irc.reply('For this round, the categories are...', prefixNick=False)
                    self.gamecard = filter(None, random.choice(self.gamecards).splitlines())
                    for x in self.gamecard:
                        irc.reply(x, prefixNick=False)
                    schedule.addEvent(chooseLetter, time.time() + 5)

                def chooseLetter():
                    self.letter = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                    irc.reply('The letter for this round is... %s' % self.letter, prefixNick=False) 
                    irc.reply('You have 90 seconds starting right meow!', prefixNick=False)
                    self.catsplaying = True

                    for x in self.players:
                        for y in self.gamecard:
                            irc.sendMsg(ircmsgs.privmsg(x, y))
                        irc.sendMsg(ircmsgs.privmsg(x, 'Your answer must match the category and start with %s. Reply in format: # answer' % self.letter))

                    schedule.addEvent(warningOne, time.time() + 30)
                    schedule.addEvent(warningTwo, time.time() + 60)
                    schedule.addEvent(warningThree, time.time() + 80)
                    schedule.addEvent(gameEnd, time.time() + 90)

                def warningOne():
                    irc.reply('One minute remaining!', prefixNick=False)

                def warningTwo():
                    irc.reply('30 seconds left!', prefixNick=False)

                def warningThree():
                    irc.remply('10 seconds! Hurry!', prefixNick=False)

                def gameEnd():
                    self.catsrunning = False
                    self.catsplaying = False
                    irc.reply('Game over!', prefixNick=False)
                    irc.reply('Results:', prefixNick=False)

                    m = max(len(x) for x in self.gamecard)

                    for k, v in self.players.iteritems():
                        v['m'] = max(len(v.get(i, '-')) for i in range(1,13))

                    for i in xrange(1,13):
                        r = '%-*s (%s)' % (m, self.gamecard[i], ', '.join(['%s:%-*s' % (k, v['m'], v.get(i, '-')) for k,v in self.players.iteritems()]))
                        answers = [x[i] for x in self.players.itervalues() if i in x]
                        r += ' +1 '
                        w = []
                        for n,x in self.players.iteritems():
                            if i in x and answers.count(x[i]) == 1:
                                x['score'] += 1
                                w.append(n)
                        if w:
                            r += ', '.join(w)
                        else:
                            r += 'nobody :('
                        irc.reply(r, prefixNick=False)

                    for n,x in self.players.iteritems():
                        irc.reply('Total score for %s: %s' % (n, x['score']), prefixNick=False)

                    self.players = {}

                schedule.addEvent(listCats, time.time() + 30)

    cats = wrap(cats)

    def jcats(self, irc, msg, args):
        """docstring"""
        if msg.args[0] == self.gamechan:
            if self.catsjoining is True:
                if msg.nick in self.players:
                    irc.error('You have already joined the round!')
                else:
                    self.players[msg.nick] = {'score': 0}
                    irc.replySuccess()
            else:
                irc.error('You can\'t join right now')

    jcats = wrap(jcats)

    def doPrivmsg(self, irc, msg):
        if self.catsplaying and msg.args[0].lower() == irc.nick.lower() and msg.nick in self.players:
            parts = msg.args[1].split(None, 1)
            if len(parts) == 2 and parts[0].isdigit():
                i = int(parts[0])
                if i > 0 and i < 13:
                    if parts[1][0].upper() == self.letter:
                        self.players[msg.nick][i] = parts[1].lower()
                    else:
                        irc.queueMsg(ircmsgs.privmsg(msg.nick, 'Rejected %s. The answer must start with %s!' % (parts[1], self.letter)))

Class = Cats

# vim:set shiftwidth=4 softtabstop=4 expandtab:
