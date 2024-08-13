const map = new maplibregl.Map({
    container: 'map',
    style:
        'https://api.maptiler.com/maps/streets/style.json?key=get_your_own_OpIi9ZULNHzrESv6T2vL',
    center: [2,48],
    zoom: 2,
    minZoom:2
});

map.addControl(new maplibregl.NavigationControl());
let monElement = document.getElementById('lvl');
const spin = document.querySelector('.loading')

map.on('zoom', onMapZoom);

map.on('click', onMapClick);

function onMapClick(e) {
  // const bounds = map.getBounds()
  // const topRight = bounds.getNorthEast();
  // const bottomLeft = bounds.getSouthWest();

  // console.log("MAP BOUNDS : ", topRight, bottomLeft);
  // console.log(e.lngLat)

}


function onMapZoom(e) {
    monElement.innerHTML = Math.floor(map.getZoom()*100)/100;
};

let app = Vue.createApp({
  data() {
    return {
      puntos: null,
      layersIDs: [],
      countryName:'',
      lst:[],
      categorySelected: [],
      algoSelected:'',
      layersOnMap: [],
      dicoBounds: null,
      selection: false, // v-for apply algo
      isDisabled: false, // disable display of category layer
      paramAlgos:{'LabelGrid':{'width':0.5, 'mode':'aggregation'},
                  'Swing':{'arm':8}, 
                  'Quadtree':{'depth':2,'type':'aggregation'},
                  'Delaunay':{'minlength':2},
                  'K-means':{'shrink_ratio':0.25},
                  'Initial Point':""
                  },
    };
  },
  mounted(){
    fetch('/lstNames')
    .then(result => result.json())
    .then(r => {
      this.lst = r;
    });
  },

  methods: {

    hello(){
      console.log("hello !");
    },

    process(){
      spin.style.display = "block";

      if (this.algoSelected.length != 0){
        let donnees = new FormData();
        donnees.append('country', this.countryName);
        donnees.append('category', this.categorySelected);
        donnees.append('bounds', JSON.stringify(this.dicoBounds));
        donnees.append('algoSelected', this.algoSelected);
        donnees.append('algoParams', JSON.stringify(this.paramAlgos[this.algoSelected]))

        fetch('/algoGrid', {
            method: 'post',
            body: donnees,
        })
        .then(reponseHTTP => reponseHTTP.json())
        .then(resultat => {
            this.puntos = resultat['new'];
            hideLayers();

            if (typeof map.getLayer('new') !== 'undefined') {
              map.removeLayer('new').removeSource('new');
              this.layersIDs = this.layersIDs.filter(e => e !== 'new');
              map.removeLayer('grid').removeSource('grid');
              this.layersIDs = this.layersIDs.filter(e => e !== 'grid');
            };
            addDataPoly("grid", resultat['grid'], 'green');
            addData("new", resultat['new'], 'gold');
            this.isDisabled = true;
            spin.style.display = "none";

        })
      }
    },

    downloadJson: function() {
      const jsonData = JSON.stringify(this.puntos);
      const file = new Blob([jsonData], {type: 'application/geojson'});
      const a = document.createElement('a');
            a.href = URL.createObjectURL(file);
            let dico = app.paramAlgos[app.algoSelected];
            const key = Object.keys(dico)[0];
            const val = dico[key];
            a.download = this.countryName+"_"+this.algoSelected+"_"+key+val+".geojson";
            a.click();
    },

    showAllPuntos() {
      this.clearData();
      clearLayers();
      spin.style.display = "block";
      fetch("/data")
      .then(function(response) {
      return response.json();
      })
      .then(function(data) {
        
        addData("presumptive_mapdata", data['c'], 'dodgerblue');
        addData("known_mapdata", data['b'], 'red');
        addData("user_mapdata", data['a'], 'purple');

        spin.style.display = "none";
      });
      this.countryName = "";
    },

    puntosRegions(){
      this.algoSelected='';
      const bounds = map.getBounds()
      this.dicoBounds = {'topRight':bounds.getNorthEast(), 'bottomLeft':bounds.getSouthWest()};
      let donnees = new FormData();
      donnees.append('bounds', JSON.stringify(this.dicoBounds));
      donnees.append('country', this.countryName);

      fetch('/regions', {
          method: 'post',
          body: donnees,
      })
      .then(reponseHTTP => reponseHTTP.json())
      .then(resultat => {
          this.puntos = resultat;
          clearLayers();
          addAll(resultat, this.countryName);
          this.clearData();

      })
    },

    autocomplete() {
      this.algoSelected='';
      this.dicoBounds=null;
      let donnees = new FormData();
      donnees.append('recherche', this.countryName);

      fetch('/pays', {
          method: 'post',
          body: donnees,
      })
      .then(reponseHTTP => reponseHTTP.json())
      .then(resultat => {
          this.puntos = resultat;
          clearLayers();
          addAll(resultat, this.countryName);
          this.clearData();

      })
    },

    showSelectedLayers(){
      hideLayers();
      this.layersOnMap.map(layer => {
        if (layer == this.countryName+this.categorySelected){
          map.setLayoutProperty(this.countryName+this.categorySelected, 'visibility', 'visible');
        };
        if (layer == "new"){
          map.setLayoutProperty("new", 'visibility', 'visible');
        };
        if (layer == "grid"){
          map.setLayoutProperty("grid", 'visibility', 'visible');
        };

      });
    },

    showCategoryLayers(){
      hideLayers();
      let layerName = this.countryName+this.categorySelected[0];

      if (typeof map.getLayer(layerName) !== 'undefined') {
        this.categorySelected.map(layer => {
          map.setLayoutProperty(this.countryName+layer, 'visibility', 'visible');
        });
      };

      if (this.categorySelected.length == 1 && this.layersIDs.includes(layerName)){
        this.selection = true;
      }
      else {
        this.selection = false;
      }
    },

    clearData(){
      this.isDisabled = false;
      this.selection = false;
      this.categorySelected = [];
      this.layersOnMap = [];
    },
  },

}).mount('#app');


function addData(name, jsonData, color){
  map.addSource(name, {
    type: 'geojson',
    data: jsonData
  });
  if (app.algoSelected === 'Delaunay' || app.algoSelected === 'Swing'){
    map.addLayer({
      id: name,
      type: "fill",
      source: name,
      paint: {
        'fill-color': color,
        'fill-opacity': 0.8
      }
    });
  }
  else{
    map.addLayer({
      id: name,
      type: "circle",
      source: name,
      paint: {
        "circle-color": color,
        "circle-radius": ['coalesce',['get', 'radius'], 2],
        "circle-stroke-width": 0.6,
        "circle-stroke-color": "black",
      }
    });
  }
  app.layersIDs.push(name);
}

function addDataPoly(name, jsonData, color){
  map.addSource(name, {
    type: 'geojson',
    data: jsonData
  });
  map.addLayer({
    id: name,
    type: "fill",
    source: name,
    paint: {
      'fill-color': color,
      'fill-opacity': 0.4,
      "fill-outline-color": "black"
    }
  });
  app.layersIDs.push(name);
};


function addAll(data, name){
  addData(name + "presumptive_mapdata", data['presumptive_mapdata'], 'dodgerblue');
  addData(name + "known_mapdata", data['known_mapdata'], 'red');
  addData(name + "user_mapdata", data['user_mapdata'], 'purple');
}

function hideLayers(){
  if (app.layersIDs) {
    app.layersIDs.map(id => {
      map.setLayoutProperty(id, 'visibility', 'none');
    });
  }
}

function clearLayers(){
  if (app.layersIDs) {
    app.layersIDs.map(id => {
      map.removeLayer(id);
      map.removeSource(id);
    });
  }
  app.layersIDs = [];
}