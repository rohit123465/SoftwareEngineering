import article
import unittest
import requests
from datetime import datetime

class WSTArticleTestCase(unittest.TestCase):
    testarticle: article.Article
    def setUp(self):
        self.testarticle = article.Article("https://finance.yahoo.com/news/west-pharmaceutical-services-inc-president-043138258.html", requests.Session())
    def test_title(self):
        assert self.testarticle.title == "West Pharmaceutical Services Inc President and CEO Eric Green Sells Company Shares"
    def test_url(self):
        assert self.testarticle.url == "https://finance.yahoo.com/news/west-pharmaceutical-services-inc-president-043138258.html"
    def test_author(self):
        assert self.testarticle.author == "GuruFocus Research"
    def test_date(self):
        assert self.testarticle.date == datetime(2024, 3, 1, 4, 31, 38)
    def test_eval(self):
        assert self.testarticle.evaluation >= 0 and self.testarticle.evaluation <= 1

class PLDArticleTestCase(unittest.TestCase):
    testarticle: article.Article
    def setUp(self):
        self.testarticle = article.Article("https://finance.yahoo.com/news/prologis-stock-buy-141800671.html", requests.Session())
    def test_title(self):
        assert self.testarticle.title == "Is Prologis Stock a Buy?"
    def test_url(self):
        assert self.testarticle.url == "https://finance.yahoo.com/news/prologis-stock-buy-141800671.html"
    def test_author(self):
        assert self.testarticle.author == "Reuben Brewer, The Motley Fool"
    def test_date(self):
        assert self.testarticle.date == datetime(2024, 3, 2, 14, 18)
    def test_eval(self):
        assert self.testarticle.evaluation >= 0 and self.testarticle.evaluation <= 1

class MDTArticleTestCase(unittest.TestCase):
    testarticle: article.Article
    def setUp(self):
        self.testarticle = article.Article("https://finance.yahoo.com/news/insulet-sizes-competition-tandem-medtronic-121200744.html", requests.Session())
    def test_title(self):
        assert self.testarticle.title == "Insulet sizes up competition as Tandem, Medtronic plan new insulin patch-pumps"
    def test_url(self):
        assert self.testarticle.url == "https://finance.yahoo.com/news/insulet-sizes-competition-tandem-medtronic-121200744.html"
    def test_author(self):
        assert self.testarticle.author == "Elise Reuter"
    def test_date(self):
        assert self.testarticle.date == datetime(2024, 2, 29, 12, 12)
    def test_eval(self):
        assert self.testarticle.evaluation >= 0 and self.testarticle.evaluation <= 1