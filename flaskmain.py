# import main Flask class and request object
import json

from flask import Flask, request

# create the Flask app
from main import main

app = Flask(__name__)


@app.route('/githubinfo')
def get_github_info():
    githubID = request.args.get("githubID")
    return json.dumps(main(githubID))


@app.route('/form-example')
def form_example():
    return 'Form Data Example'


@app.route('/json-example')
def json_example():
    return 'JSON Object Example'


if __name__ == '__main__':
    # run app in debug mode on port 5000
    app.run(debug=True, port=5000)
