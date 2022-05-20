# libraries
import urllib.request
from bs4 import BeautifulSoup
import csv
# Put your URL here
url = 'https://www.nytimes.com/books/best-sellers/combined-print-and-e-book-nonfiction/'
# Fetching the html
request = urllib.request.Request(url)
content = urllib.request.urlopen(request)
# Parsing the html 
parse = BeautifulSoup(content, 'html.parser')
# Provide html elements' attributes to extract the data 
text1 = parse.find_all('h3', attrs={'class': 'css-5pe77f'})
text2 = parse.find_all('p', attrs={'class': 'css-hjukut'})
# Writing extracted data in a csv file
with open('index.csv', 'a') as csv_file:
  writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
  writer.writerow(['Title','Author'])
  for col1,col2 in zip(text1, text2):
    writer.writerow([col1.get_text().strip(), col2.get_text().strip()])
