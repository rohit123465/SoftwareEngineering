import time
import requests
import unittest
from company import Company

class TestCompany(unittest.TestCase):
    def __init__(self, methodName: str = "runTest", symbol:str='AAL') -> None:
        super(TestCompany,self).__init__(methodName)
        self.s = requests.Session()
        self.company = Company(symbol, self.s)

    def test_init(self):
        self.assertIsNotNone(self.company.articles)
        for item in self.company.articles:
            print(item.url)
            
    def test_no_articles(self):
        company_with_no_articles = Company('DIG.L', self.s)
        self.assertEqual(len(company_with_no_articles.articles), 0)

    def test_one_to_seven_articles(self):
        company_with_few_articles = Company('SHRS.L', self.s)
        self.assertTrue(0 < len(company_with_few_articles.articles) < 8)

    def test_more_than_eight_articles(self):
        company_with_many_articles = Company('MSFT', self.s)
        self.assertTrue(len(company_with_many_articles.articles) >= 8)

    def test_companies_from_different_exchanges(self):
        nasdaq_company = Company('GOOG', self.s)
        nyse_company = Company('DB', self.s)
        self.assertIsNotNone(nasdaq_company.articles)
        self.assertIsNotNone(nyse_company.articles)
     
    def test_update_articles(self):
        original_articles = self.company.articles
        self.company.update(self.s)
        updated_articles = self.company.articles
        self.assertTrue(all(article in updated_articles for article in original_articles))
        self.assertEqual(len(updated_articles), len(set(updated_articles)))

if __name__ == '__main__':
    unittest.main()
