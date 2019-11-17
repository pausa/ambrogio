<template>
  <div id = "clock">
    <p class="date">{{ day }}</p>
    <p>{{ time }}</p>
    <p class="date">{{ date }}</p>
  </div>
</template>
<script>
var days = [
    'DOMENICA', 
    'LUNEDI',
    'MARTEDI',
    'MERCOLEDI',
    'GIOVEDI',
    'VENERDI',
    'SABATO',
];
export default {
    data: function () {
        return {
            day: 'TOD',
            time: 'tick tock',
            date: 'now this year',
            timerId: ''
        }
    },
    mounted: function () {
        this.timerId = setInterval(this.updateTime, 1000);
        this.updateTime();
    },
    methods: {
        updateTime: function() {
            var d = new Date();
            this.day = days[d.getDay()]
            this.time = `${this.pad(d.getHours(),2)}:${this.pad(d.getMinutes(),2)}:${this.pad(d.getSeconds(),2)}`;
            this.date = `${this.pad(d.getFullYear(),4)}-${this.pad(d.getMonth() + 1,2)}-${this.pad(d.getDate(),2)}`;
        },
        pad: function(num, digit) {
            var zero = '';
            for(var i = 0; i < digit; i++) {
                zero += '0';
            }
            return (zero + num).slice(-digit);
        }
    }
}

</script>
<style>
.date{
    font-size: 40%
}
</style>