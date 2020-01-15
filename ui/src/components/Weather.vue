<template>
  <div id = "weather">
    <!-- TODO proper degree sign -->
    <div class="tembox">
      <div class="max">{{max}}&deg;</div>
      <div class="min">{{min}}&deg;</div>
    </div>
    <div class="tembox">{{temp}}&deg;</div>
    <i class="tembox wi" 
       :style = "wstyle"
       :class="wicon"/>
    <!-- TODO CHART -->
  </div>
</template>
<script>
const icons = new Map([
 ['clear-day','wi-day-sunny'],
 ['partly-cloudy-day','wi-day-cloudy'],
 ['clear-night','wi-night-clear'],
 ['partly-cloudy-night','wi-night-alt-cloudy'],
 ['rain','wi-rain'],
 ['snow','wi-snow'],
 ['sleet','wi-sleet'],
 ['wind','wi-strong-wind'],
 ['fog','wi-fog'],
 ['cloudy','wi-cloudy']
]);
const colors = new Map([
 ['clear-day','yellow'],
 ['partly-cloudy-day','yellow'],
 ['clear-night','blue'],
 ['partly-cloudy-night','blue'],
 ['rain','cyan'],
 ['snow','white'],
 ['sleet','white'],
 ['wind','grey'],
 ['fog','grey'],
 ['cloudy','grey']
]);
const deficon='wi-alien';
const defcolor='green';

export default {
    props: ['min', 'max', 'temp', 'icon'],
    computed: {
      wicon: function(){
        return icons.get(this.icon) || deficon;
      },
      wstyle: function(){
        return {color: colors.get(this.icon) || defcolor};
      }
    }
}

</script>
<style>
@import '~weather-icons/css/weather-icons.css';
.tembox{
  width: 30%;
  padding: 5px;
  display: inline-block;
  vertical-align: middle;
  text-align: center;
}
.max{
  font-size: 40%;
  vertical-align: top;
  color: red;
}
.min{
  font-size: 40%;
  color: cyan;
  vertical-align: bottom;
}
</style>