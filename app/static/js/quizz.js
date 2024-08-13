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
  let zl = Math.floor(map.getZoom()*100)/100;
  console.log(map.getZoom())
}


let app = Vue.createApp({
  data() {
    return {
      count:-1,
      data:null,
      question:"",
      selectedOptions:[],
      tab:null,
      answers:[],
    };
  },

  created(){
    fetch('/dataQuizz')
    .then(result => result.json())
    .then(r => {
      this.data = r;
    });
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
    download() {
      let dico = dicoToFormatCSV({a:1, b:2});
      const file = new Blob([dico], {type: 'text/csv;charset=utf-8,'});
      const a = document.createElement('a');
            a.href = URL.createObjectURL(file);
            a.download = "rep.csv";
            a.click();
    },

    suiv(){
      let maxi = 3;
      this.count++;
      if(this.count>maxi){
        this.count = maxi;
      }
      this.question = this.data.question[this.count];
      console.log(this.selectedOptions)
    },

    prev(){
      this.count--;
      if (this.count<0){
        this.count = 0;
      }
      this.question = this.data.question[this.count];
    },

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
