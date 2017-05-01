import sys
from flask import Flask
from bottlereact import BottleReact

PROD = '--prod' in sys.argv

app = Flask(__name__)
br = BottleReact(app, prod=PROD)

@app.route('/')
def root():
  return br.render_html(
    br.HelloWorld({'name':'World'})
  )

# run with:
# FLASK_APP=run_flask.py python3 -m flask run
