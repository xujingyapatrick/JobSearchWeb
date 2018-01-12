import pymongo
import pprint
import nltk
import logging
from pymongo import MongoClient
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.lancaster import LancasterStemmer
from gensim import corpora, models, similarities
import json

class Rec():
	def __init__(self, jobtype):
		self.init_matrix(jobtype)


	def init_matrix(self, jobtype):
		logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
		client = MongoClient('localhost', 27017)
		db = client.indeed
		jobs = db[jobtype]
		docs = jobs.find()

		descs = []
		self.titles = []
		self.urls = []
		self.company = []
		for doc in docs:
			descs = descs + [doc['desp']]
			self.titles = self.titles + [doc['title']]
			self.urls = self.urls + [doc['detailUrl']]
			self.company = self.company + [doc['company']]

		texts_tokenized = [[word.lower() for word in word_tokenize(document)] for document in descs]

		# collect public keywords
		self.keywords = dict()
		with open("techDict.txt") as f:
			content = f.readlines()
		for c in content:
			self.keywords[c.lower().strip()] = 1

		texts = [[word for word in docment if word in self.keywords] for docment in texts_tokenized]

		self.dictionary = corpora.Dictionary(texts)

		# get bag-of-words
		corpus = [self.dictionary.doc2bow(text) for text in texts]
		tfidf = models.TfidfModel(corpus)
		corpus_tfidf = tfidf[corpus]
		# wrap the corpus with lsi. (corpus: bow->tfidf->fold-in-lsi)
		self.lsi = models.LsiModel(corpus_tfidf, id2word=self.dictionary, num_topics=100)
		# self.lsi.save('/tmp/model.lsi')  # same for tfidf, lda, ...
		# self.lsi = models.LsiModel.load('/tmp/model.lsi')
		self.index = similarities.MatrixSimilarity(self.lsi[corpus])
	
	def txt2feature(self,doc):
		f = [word.lower() for word in word_tokenize(doc)]
		f = [word for word in f if word in self.keywords]
		return f


	def recommend(self,data):
		# with open("test_data.txt") as f:
		# 	test = f.read().decode('utf-8')
		keywords = self.txt2feature(data)
		bow = self.dictionary.doc2bow(keywords)
		ml_lsi = self.lsi[bow]

		sims = self.index[ml_lsi]
		sort_sims = sorted(enumerate(sims), key=lambda item: -item[1])
		res = []
		i = 0
		for item in sort_sims[0:min(50,len(sort_sims))]:
			index = item[0]
			res = res + [ {"index": i ,"url":self.urls[index], "title" : self.titles[index], "company" : self.company[index]} ]
			i = i + 1 
		return res