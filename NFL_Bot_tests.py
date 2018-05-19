import unittest
import NFL_Bot

class MatchTestMethods(unittest.TestCase):
    def testSingle(self):
        d = dummyComment("_[[brandon marshall (wr)]]")
        self.assertEqual(NFL_Bot.getMatches(d),[("brandon marshall", "wr")])
        d = dummyComment("__*$@tombrady__ tom brady[tom brady][[]tm brady]"+\
            "[tom brady[]][[(tom brady)]][[brandon marshall(lb)]]")
        self.assertEqual(NFL_Bot.getMatches(d),[("brandon marshall", "lb")])

    def testMultiple(self):
        d = dummyComment("[[brandon marshall]]")
        self.assertEqual(NFL_Bot.getMatches(d), [("brandon marshall", '')])
        d = dummyComment("[[brandon marshall (wr)]][[Brandon marshall (lb)]]")
        self.assertEqual(NFL_Bot.getMatches(d), [("brandon marshall", 'wr'),\
            ("Brandon marshall", 'lb')])

class CommentWriteTestMethods(unittest.TestCase):
        bWR="**Name:** [Brandon Marshall]"+\
            '(https://www.pro-football-reference.com/players/M/MarsBr00.htm)'+\
            "\n**Height:** 6-4\n**Weight:** 229lb\n**Team:** Free Agent" +\
            "\n**Date of Birth:** March 23, 1984\n" +\
            "SUMMARY|G|AV|Rec|Yds|Y/R|TD|FantPt\n"+\
            ":--|:--|:--|:--|:--|:--|:--|:--\n"+\
            "2017|5|1|18|154|8.6|0|15.4\n"+\
            "Career|172|104|959|12215|12.7|82|1712.3\n\n\n\n"

        bLB="**Name:** [Brandon Marshall]" +\
            '(https://www.pro-football-reference.com//players/M/MarsBr01.htm)'+\
            "**Height:** 6-1\n\n**Weight:** 250lb\n\n" + \
            "**Team:** [Denver Broncos]"+ \
            '(https://www.pro-football-reference.com/teams/den/2018.htm)\n\n'+\
            "**Date of Birth:** September 10, 1989" + \
            "SUMMARY|G|AV|Sk|Tkl|FF\n"+\
            ":--|:--|:--|:--|:--|:--\n"+\
            '2017|16|8|3.0|75|1\n'+\
            'Career|63|29|6.5|288|5\n\n\n\n'

        def testSingle(self):
            url='https://www.pro-football-reference.com/players/M/MarsBr01.htm'
            player = NFL_Bot.Player(url)
            nameString = "[Brandon Marshall](https"+\
                "://www.pro-football-reference.com/players/M/MarsBr01.htm)"
            self.assertEqual(player.NameString, nameString)
            self.assertEqual(player.Height, "6-1")
            self.assertEqual(player.Weight, "250lb")
            self.assertEqual(player.Team, "Denver Broncos")
            self.assertEqual(player.DOB, "September 10,\xa01989")
            statsString="SUMMARY|G|AV|Sk|Tkl|FF\n"+\
                        ":--|:--|:--|:--|:--|:--\n"+\
                        '2017|16|8|3.0|75|1\n'+\
                        'Career|63|29|6.5|288|5\n\n\n\n'
            self.assertEqual(str(player.Stats), statsString)

class UrlFindTestMethods(unittest.TestCase):
        def testSingle(self):
            self.assertEqual(NFL_Bot.getPlayerURLs("ben roethlisberger", '')[0],\
                'https://www.pro-football-reference.com/players/R/RoetBe00.htm')

        def testPosition(self):
            self.assertEqual(NFL_Bot.getPlayerURLs("brandon marshall", 'wr')[0],\
                'https://www.pro-football-reference.com/players/M/MarsBr00.htm')

        def testMultiple(self):
            re=['https://www.pro-football-reference.com/players/G/GrubBe20.htm'\
               ,'https://www.pro-football-reference.com/players/H/HartBe00.htm'\
               ,'https://www.pro-football-reference.com/players/N/NollBe20.htm']
            self.assertEqual(NFL_Bot.getPlayerURLs("ben r", ''), re)

        def testMultipleWithPos(self):
            re=['https://www.pro-football-reference.com/players/G/GrubBe20.htm'\
               ,'https://www.pro-football-reference.com/players/N/NollBe20.htm'\
               ,'https://www.pro-football-reference.com/players/B/BentRo20.htm']
            self.assertEqual(NFL_Bot.getPlayerURLs("ben r", "g"), re)


class dummyComment:
    def __init__(self, text):
        self.body = text


if __name__ == '__main__':
    unittest.main()
