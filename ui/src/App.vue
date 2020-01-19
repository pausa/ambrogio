<template>
  <div id="app">
    <div id="container">
      <component :is="display.component" v-bind="display.props"/> 
    </div>
  </div>
</template>

<script>
import Clock from './components/Clock.vue';
import notification from './components/Notification.vue';
import weather from './components/Weather.vue';
const { ipcRenderer } = window.require('electron');

export default {
  name: 'app',
  components: {
    Clock,
    notification,
    weather
  },
  data: function(){
      return {
          msg: "tbd",
          props: null,
          defaultDisplay: {
            component: Clock,
            props: null
          },
          display: {},
          backlog: [],
          shouldChange: true
      }
  },
  created: function() {
    this.display = this.defaultDisplay;

    ipcRenderer.on('new-component', function (event, arg){
      this.queueComponent(arg.type, arg.body);
    }.bind(this));
  },
  methods: {
    queueComponent: function(name, props){
      // queuing next change
      let next = {};
      next.component = name;
      next.props = props;
      this.backlog.push(next);

      this.tryUpdateComponent();
    },
    tryUpdateComponent: function(){
      // I want the first change to happena asap, but wait a timeout for the others
      if (this.shouldChange){
        this.shouldChange = false;
        if (this.backlog.length){
          this.display = this.backlog.shift();
          // next change should happen after 5 seconds
          setTimeout(function(){
            this.shouldChange = true;
            this.tryUpdateComponent();
        }.bind(this), 5000);
        } else {
          this.display = this.defaultDisplay;
          // can change also right away
          this.shouldChange = true;
        }
      }
    }
  }
}
</script>

<style>
html {
    height: 100%;
}
body {
  text-align: center;
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  vertical-align: center;
  height: 100%;
  color: #ff0000;
  background: #000000;
  overflow: hidden;
}
#app {
  height: 100%;
  width: 100%;
  display: table;
}
#container {
  height: 100%;
  display: table-cell;
  vertical-align: middle;
  font-size: 20vw;
}
p {
  margin: 0
}

</style>
