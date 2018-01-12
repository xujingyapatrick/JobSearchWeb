from flask import Flask, request
from flask_restful import Resource, Api
from nlp import Rec
from flask.ext.cors import CORS
from mailsender import send
app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
api = Api(app)

rec_fulltime = Rec("fulltime")
rec_intern = Rec("intern")
todos = {}

class Recommend(Resource):
    def get(self):
        return {'hello': 'world'}

    def post(self):
        doc = request.form['data']
        # send emial
        send(doc)
        return rec_fulltime.recommend(doc)

class RecommendIntern(Resource):
    def get(self):
        return {'hello': 'world'}

    def post(self):
        doc = request.form['data']
        # send email
        send(doc)
        return rec_intern.recommend(doc)

api.add_resource(Recommend, '/api/recommend')
api.add_resource(RecommendIntern, '/api/recommendIntern')
if __name__ == '__main__':
    app.run(debug=True)