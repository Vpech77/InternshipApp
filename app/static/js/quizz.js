const map = new maplibregl.Map({
    container: 'map',
    style:
        'https://api.maptiler.com/maps/streets/style.json?key=get_your_own_OpIi9ZULNHzrESv6T2vL',
    center: [10, 48],
    zoom: 3.5,
    minZoom:3
});
map.addControl(new maplibregl.NavigationControl());

map.on('zoom', onMapZoom);

function onMapZoom(e) {
 
}


let app = Vue.createApp({
  data() {
    return {
      IsStart:false,
      count:0,
      data:null,
      tab:null, // data.options
      question:"",
      selectedOptions:[],
      answer:"",
      dicoAnswers:{},
      time:null,
    };
  },

  created(){
    fetch('/dataQuizz')
    .then(result => result.json())
    .then(r => {
      this.data = r;
    });
  },

  mounted(){
    fetch("/data")
    .then(function(response) {
    return response.json();
    })
    .then(function(data) {
      
      addData("presumptive_mapdata", data['c'], 'dodgerblue');
      addData("known_mapdata", data['b'], 'red');
      addData("user_mapdata", data['a'], 'purple');

    })
  },
  watch: {
    time(val){
      if (val === '00:00'){
        this.suiv();
      }
    }

  },

  computed: {
    isInputOption() {
      if (this.data.options[this.count] !== undefined){
        this.tab = this.data.options[this.count];
      }
      return this.tab === null;
    },
    txt(){
      return "Question " + this.count;
    }
  },

  methods: {
    start(){
      this.IsStart = true;
      this.question = this.data.question[this.count];
      timer(this.data.time[this.count]);
    },

    download() {
      let dico = dicoToFormatCSV(this.dicoAnswers);
      const file = new Blob([dico], {type: 'text/csv;charset=utf-8,'});
      const a = document.createElement('a');
            a.href = URL.createObjectURL(file);
            a.download = "rep.csv";
            a.click();
    },

    suiv(){
      this.addAnswer();
      let maxi = 3;
      this.count++;
      if(this.count>maxi){
        this.IsStart = false;
        this.count=0;
      }
      this.maj();
    },

    addAnswer(){
      let [min, sec] = this.time.split(":");
      let secondes = parseInt(sec, 10);
      let duration = this.data.time[this.count] - secondes

      if (this.data.options[this.count] === null){
        this.dicoAnswers[this.count] = JSON.stringify({rep:this.answer, temps:duration});
      }
      else{
        this.dicoAnswers[this.count] = JSON.stringify({rep:this.selectedOptions, temps:duration});
      }
    },

    maj(){
      timer(this.data.time[this.count]);
      this.question = this.data.question[this.count];
      this.answer = "";
      this.selectedOptions = [];
    }

  },


}).mount('#app');


function dicoToFormatCSV(dico){
  const csvRows = []
  const headers = Object.keys(dico)
  csvRows.push(headers.join(';'));
  const values = Object.values(dico).join(';');
  csvRows.push(values)
  return csvRows.join('\n');
}

let minuteur;

function timer(temps){
  app.time = "";
  clearInterval(minuteur);
  minuteur = setInterval(() => {
    let minutes = parseInt(temps / 60, 10)
    let secondes = parseInt(temps % 60, 10)
  
    minutes = minutes < 10 ? "0" + minutes : minutes
    secondes = secondes < 10 ? "0" + secondes : secondes
    app.time = `${minutes}:${secondes}`
    temps = temps <= 0 ? 0 : temps - 1
  }, 1000)
}

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
};