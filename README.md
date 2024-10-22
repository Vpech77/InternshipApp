# Multi-scale generalization of massive point data

[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Vue.js](https://img.shields.io/badge/vuejs-%2335495e.svg?style=for-the-badge&logo=vuedotjs&logoColor=%234FC08D)](https://vuejs.org/)
[![MapLibre Badge](https://img.shields.io/badge/MapLibre-396CB2?logo=maplibre&logoColor=fff&style=for-the-badge)](https://maplibre.org/maplibre-gl-js/docs/)
[![PostgreSQL Badge](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=fff&style=for-the-badge)](https://www.postgresql.org/)

In this repository, you'll find a Flask-based web app for cartographic generalization that I developed during my 3-month internship in the LostInZoom research team. The primary goal of this app is to assist in creating a multi-scale web map, utilizing point generalization algorithms from the Python library, Cartagen.

# ⚙️ Installation ⚙️

Clone the project

```bash
  git clone https://github.com/Vpech77/InternshipApp.git
```

Next, restore the PostgreSQL backup all_puntos.sql

To restore the PostgreSQL backup into your database, ensure you have PostgreSQL version 16 or higher, along with a properly configured PostGIS extension.

## 🛠 Requirements 🛠

[![Flask](https://img.shields.io/badge/Flask-v2.2.5-0bacda?logo=flask&logoColor=fff&style=plastic)](https://flask.palletsprojects.com/)
[![Cartagen](https://img.shields.io/badge/Cartagen-v1.0.0-blue?logo=python&logoColor=white&style=plastic)](https://cartagen.readthedocs.io/en/latest/)
[![GeoPandas Badge](https://img.shields.io/badge/GeoPandas-v0.14.4-139C5A?logo=geopandas&logoColor=fff&style=plastic)](https://geopandas.org/en/stable/)
[![psycopg2](https://img.shields.io/badge/psycopg2-v2.9.9-yellow?logo=python&logoColor=white&style=plastic)](https://www.psycopg.org/)

To install all the required Python libraries, run the following command:

```bash
pip install -r requirements.txt
```
# 🚀 Run 🚀

Run the application 

```python
  python app.py
```

Now head over to http://127.0.0.1:5000/, and you should see the application running on your navigator.



