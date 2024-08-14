const map = new maplibregl.Map({
    container: 'map',
    style:
        'https://api.maptiler.com/maps/streets/style.json?key=get_your_own_OpIi9ZULNHzrESv6T2vL',
    center: [2, 48],
    zoom: 2,
    minZoom:2
});
map.addControl(new maplibregl.NavigationControl());

map.on('zoom', onMapZoom);

function onMapZoom(e) {

  let zl = Math.floor(map.getZoom());
  console.log(map.getZoom())
  app.zl = 'ZoomLevel : '+ zl;
  showZoomLayer();
}

function addZoomLayers(){
  fetch("/newData")
  .then(function(response) {
  return response.json();
  })
  .then(function(data) {
    let zoomPoly = 4;
    for (let i=2; i<zoomPoly+1; i++){
      addDataPoly("zoom"+i, data['zoom'+i], 'red');
    }
    let zoomPuntos = 9;
    for (let i=zoomPoly+1; i<zoomPuntos+1; i++){
      addData("zoom"+i, data['zoom'+i], 'red');
    }
    addData("zoom3bis", data['zoom3bis'], 'red')
    addData("zoom4bis", data['zoom4bis'], 'red')
    hideLayers();
  });
}

function showZoomLayer(){
  let zl = Math.floor(map.getZoom());
  let layerName = "zoom"+zl;
  if (typeof map.getLayer(layerName) !== 'undefined'){
    hideLayers();
    map.setLayoutProperty(layerName, 'visibility', 'visible');
    if (zl===3){
      map.setLayoutProperty("zoom3bis", 'visibility', 'visible');
    }
    if (zl===4){
      map.setLayoutProperty("zoom4bis", 'visibility', 'visible');
    }
  }
  else{
    hideLayers();
  }
}

let app = Vue.createApp({
  data() {
    return {
      puntos: null,
      zl:'ZoomLevel : 2',
      layersIDs: [],
      layersOnMap:[],
      isDisabled:false,
      categorySelected: ["known_mapdata", "new"],
    };
  },
  
  mounted(){
    fetch("/data")
    .then(function(response) {
    return response.json();
    })
    .then(function(data) {
      // addData("presumptive_mapdata", data['c'], 'dodgerblue');
      addData("known_mapdata", data['b'], 'red');
      addZoomLayers();
      // addData("user_mapdata", data['a'], 'purple');
      // fetch("/newData")
      // .then(function(response) {
      // return response.json();
      // })
      // .then(function(data) {
      //   addDataPoly("new", data['zoom2'], 'red');
      // });
    });
  },

  methods: {
    hello(){
      console.log("hello !");
    },

    showCategoryLayer(){
      hideLayers();
      this.categorySelected.map(layer => {
        map.setLayoutProperty(layer, 'visibility', 'visible');
      });
    },

    newMap(){
      // hideLayers();
      // if (this.layersIDs.length == 1){
      //   fetch("/newData")
      //   .then(function(response) {
      //   return response.json();
      //   })
      //   .then(function(data) {
      //     addDataPoly("zoom2", data['zoom2'], 'red');
      //     addDataPoly("zoom3", data['zoom3'], 'red');
      //     // addData("zoom4", data['zoom4'], 'gold');
      //     // addData("zoom5", data['zoom5'], 'green');
      //   });
      // }
      // this.isDisabled = true;
    },

    showInitMap(){
      let init = ["known_mapdata"];
      hideLayers();
      init.map(layer => {
        map.setLayoutProperty(layer, 'visibility', 'visible');
      });
      this.isDisabled = false;
    }
  },

}).mount('#app');

function addData(name, jsonData, color){
  map.addSource(name, {
    type: 'geojson',
    data: jsonData
  });

  map.addLayer({
    id: name,
    type: "circle",
    source: name,
    paint: {
      "circle-color": color,
      "circle-radius": ['coalesce',['get', 'radius'], 2],
      "circle-stroke-width": 1,
      "circle-stroke-color": "black",
    }
  });
  app.layersIDs.push(name);
};

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
      'fill-opacity': 0.8,
    }
  });
  app.layersIDs.push(name);
};

function hideLayers(){
  if (app.layersIDs) {
    app.layersIDs.map(id => {
      if (id === 'known_mapdata'){

      }
      else{
        map.setLayoutProperty(id, 'visibility', 'none');
      }

    });
  }
};