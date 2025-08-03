from transformers import BertTokenizer, BertForSequenceClassification, pipeline
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import sent_tokenize
from datetime import datetime
import time

class Article:
    
    title: str
    url: str
    author: str
    date: datetime
    __contents: list[str]
    evaluation: float

    def __init__(self, url: str, session: requests.Session):
        self.url = url
        self.__contents = []

        header = { 
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
            }
        
        # getting article page html contents and filtering to only <p> tags
        t1 = time.time()
        page = session.get(url, headers = header)
        t2 = time.time()
        print("request time:", t2-t1)
        soup = BeautifulSoup(page.content, "html.parser")
        unfiltered_cont = soup.find("div", class_="caas-body")
        cont = unfiltered_cont.select("p")
        
        # 'punkt' data is a dependency for sent_tokenize, install it if not done already
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')

        # filtering out the tags and splitting into sentences
        for i in cont:
            for j in sent_tokenize(i.get_text()):
                # failsafe truncation for length >512 exceeding model's max sequence length
                j = j[:512]
                self.__contents.append(j)
        
        unfiltered_title = soup.find("div", class_="caas-title-wrapper")
        title = unfiltered_title.select("h1")
        self.title = title[0].get_text()
        
        unfiltered_author = soup.find("div", class_="caas-attr-item-author")
        author = unfiltered_author.select("span")
        self.author = author[0].get_text()
        
        unfiltered_date = soup.find("div", class_="caas-attr-time-style")
        date_format = "%Y-%m-%dT%H:%M:%S.000Z"
        self.date = datetime.strptime(unfiltered_date.select("time")[0]["datetime"], date_format)

        self.evaluation = self.__evaluate()
    
    def __evaluate(self) -> float:
        t1 = time.time()
        
        model = BertForSequenceClassification.from_pretrained("ahmedrachid/FinancialBERT-Sentiment-Analysis",num_labels=3)
        tokenizer = BertTokenizer.from_pretrained("ahmedrachid/FinancialBERT-Sentiment-Analysis")
        processor = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
        
        results: list[str] = processor(self.__contents)
        
        value: float = 0
        
        # for each positive label, increase the value by 1
        # for each negative label, decrease the value by 1
        # for neutral labels, make no change
        # average the final value by the number of entries
        for entry in results:
            if (entry["label"] == "positive"):
                value = value + 1
            if (entry["label"] == "negative"):
                value = value - 1
        
        value = value / len(results)
        
        t2 = time.time()
        print("eval time:", t2-t1)
        
        return value