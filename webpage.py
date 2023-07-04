from cgitb import text
from operator import truediv
from flask import Flask,render_template,redirect,url_for

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("temp.html",text="hello there")

if __name__ == "__main__":
    app.run(debug=True)
