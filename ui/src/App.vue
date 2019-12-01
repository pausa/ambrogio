<template>
  <div id="app">
    <div id="container">
      <component :is="component" v-bind="props"/>
    </div>
  </div>
</template>

<script>
import Clock from './components/Clock.vue';
import notification from './components/Notification.vue';
const { ipcRenderer } = window.require('electron');

export default {
  name: 'app',
  components: {
    Clock,
    notification
  },
  data: function(){
      return {
          msg: "tbd",
          component: Clock,
          props: null
      }
  },
  created: function() {
    ipcRenderer.on('new-component', function (event, arg){
      this.updateComponent(arg.type, arg.body);
    }.bind(this));
  },
  methods: {
    updateComponent: function(name, props){
      this.component = name;
      this.props = props;

      setTimeout(function(){this.component = 'Clock'}.bind(this), 5000);
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
  align: center;
  height: 100%;
  color: #ffe898;
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
