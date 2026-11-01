from pathlib import Path
from flask import Flask, jsonify
from nltk.sentiment import SentimentIntensityAnalyzer

app = Flask(__name__)
lexicon = Path(__file__).parent / 'sentiment' / 'vader_lexicon.zip'
sia = SentimentIntensityAnalyzer(lexicon_file=f'{lexicon.resolve().as_uri()}/vader_lexicon/vader_lexicon.txt')

@app.get('/')
def home():
    return jsonify(service='Best Cars Sentiment Analyzer', endpoint='/analyze/<text>')

@app.get('/analyze/<path:input_txt>')
def analyze_sentiment(input_txt):
    if len(input_txt) > 5000:
        return jsonify(error='Text is too long'), 400
    scores = sia.polarity_scores(input_txt)
    compound = scores['compound']
    sentiment = 'positive' if compound >= 0.05 else 'negative' if compound <= -0.05 else 'neutral'
    return jsonify(sentiment=sentiment, scores=scores)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
