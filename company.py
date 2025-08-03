import article
import yfinance as yf
import requests

class Company:
    name: str
    symbol: str
    industry: str
    country: str
    articles: list[article.Article]

    def __init__(self, symbol: str, session: requests.Session):
        self.symbol = symbol

        # create ticker object to extract company information
        companyTicker = yf.Ticker(symbol)

        self.name = companyTicker.info["longName"]
        self.industry = companyTicker.info["industry"]
        self.country = companyTicker.info["country"]
        self.articles = []

        # fetch and instantiate the most recent articles and store in list
        for entry in companyTicker.news:
            self.articles.append(article.Article(entry["link"], session))
    
    def update(self, session: requests.Session):
        companyTicker = yf.Ticker(self.symbol)

        urls: list[str] = []
        for a in self.articles:
            urls.append(a.url)
        for entry in companyTicker.news:
            if entry["link"] not in urls:
                self.articles.append(article.Article(entry["link"], session))