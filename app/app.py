from flask import Flask, render_template, request
import json
import os
from connect import *

app = Flask(__name__)
SITE_ROOT = os.path.realpath(os.path.dirname(__file__))

def load_geojson(filename):
    json_url = os.path.join(SITE_ROOT, "static", "data_geojson", filename)
    with open(json_url, encoding='utf-8') as json_file:
        data = json.load(json_file)
    return data

@app.route("/")
def map():
    return render_template("libreMap.html")

@app.route("/grid")
def grid():
    return render_template("grid.html")

@app.route("/visu")
def visu():
    return render_template("visu.html")

@app.route("/data")
def load_all():
    dico = {"a":load_geojson("user_all.geojson"), 
            "b":load_geojson("known_all.geojson"), 
            "c":load_geojson("presumptive_all.geojson")}
    return dico

@app.route("/newData")
def load_new():
    dico = {"zoom2":load_geojson("newMap/zoom2.geojson"),
            "zoom4":load_geojson("newMap/espagne.geojson"), 
            "zoom5":load_geojson("newMap/portugal.geojson")}
    return dico

@app.route("/pays", methods=["POST"])
def pays():
    donnees = request.form
    recherche = donnees.get('recherche')
    return select_all_puntos(recherche)

@app.route("/regions", methods=["POST"])
def regions():
    donnees = request.form
    strBounds = donnees.get('bounds')
    countryName = donnees.get('country')
    dico = {key: val for key, val in json.loads(strBounds).items()}
    return select_all_puntos_regions(dico, countryName)

@app.route("/algo", methods=["POST"])
def algo():
    donnees = request.form
    countryName = donnees.get('country')
    category = donnees.get('category')
    algoSelected = donnees.get('algoSelected')
    algoParams = donnees.get('algoParams')
    strBounds = donnees.get('bounds')
    print("----------------------------------",strBounds)
    if strBounds == 'null':
        print("here")
        dico = False
    else:
        print("rrrrrrrrrrrrrrrrrrrrrr")
        dico = {key: val for key, val in json.loads(strBounds).items()}
    res = apply_algo(countryName, dico, category, json.loads(algoParams), algoSelected)
    return res

@app.route("/algoGrid", methods=["POST"])
def algoGrid():
    donnees = request.form
    countryName = donnees.get('country')
    category = donnees.get('category')
    algoSelected = donnees.get('algoSelected')
    algoParams = donnees.get('algoParams')
    res = apply_algo(countryName, category, json.loads(algoParams), algoSelected)
    dico = {"new": res[0], "grid":res[1]}
    return dico

@app.route("/lstNames")
def test():
    return [el[0] for el in select_countryName()]

if __name__ == '__main__':
    app.run(debug=True)