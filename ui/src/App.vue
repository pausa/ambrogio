<template>
  <div id="app">
    <div id="container">
      <Clock/>
    </div>
  </div>
</template>

<script>
import Clock from './components/Clock.vue'

export default {
  name: 'app',
  components: {
    Clock
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
  background: #000000;
  color: #ffffff;
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
