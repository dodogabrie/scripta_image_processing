# -*- coding: utf-8 -*-

"""test lib.piece_issue"""


from unittest import TestCase

from maglib.piece_issue import Issue_info, Publ_year


class NextFascicleTC(TestCase):
    def test_simple(self):
        info = Issue_info.from_issue_string('7, feb., fasc. 23')
        info.publ_year = Publ_year(1932)
        next_issue = info.next_issue_info()

        self.assertEqual(next_issue.issue_n.value, 24)
        self.assertEqual(next_issue.publ_year.value, 1932)
        self.assertEqual(next_issue.month.value, 2)
        self.assertEqual(next_issue.day.value, 8)


    def test_crossyear(self):
        info = Issue_info.from_issue_string('29, feb., fasc. 2')
        info.publ_year = Publ_year(1932)
        next_issue = info.next_issue_info()

        self.assertEqual(next_issue.issue_n.value, 3)
        self.assertEqual(next_issue.publ_year.value, 1932)
        self.assertEqual(next_issue.month.value, 3)
        self.assertEqual(next_issue.day.value, 1)


    def test_range(self):
        info = Issue_info.from_issue_string('19-20, lug., fasc. 123, A. 13')
        info.publ_year = Publ_year(1968)
        next_issue = info.next_issue_info()

        self.assertEqual(next_issue.issue_n.value, 124)
        self.assertEqual(next_issue.publ_year.value, 1968)
        self.assertEqual(next_issue.month.value, 7)
        self.assertEqual(next_issue.day.value, (20, 21))
        self.assertEqual(next_issue.year.value, 13)


    def test_crossrange(self):
        info = Issue_info.from_issue_string('31-1, gen.-feb., fasc. 13, serie nuova')
        info.publ_year = Publ_year(2000)
        next_issue = info.next_issue_info()

        self.assertEqual(next_issue.issue_n.value, 14)
        self.assertEqual(next_issue.publ_year.value, 2000)
        self.assertEqual(next_issue.month.value, 2)
        self.assertEqual(next_issue.day.value, (1, 2))
        self.assertEqual(next_issue.series.value, 'serie nuova')
