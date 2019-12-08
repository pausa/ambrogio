<template>
  <div id = "notification">
    <p class="title">{{ title }}</p>
    <p class="msg">{{ normalMessage }}</p>
  </div>
</template>
<script>
export default {
    props: ['title', 'msg'],
    computed: {
      normalMessage: function(){
        let message = this.msg
          .split(" ")
          .map(word => word.length > 16 ? `[${word.substring(0, 15)}]` : word)
          .reduce(function(total, current){
            return total += " " + current;
          }, "");
        return message;
      }
    }
}

</script>
<style>
.title{
    font-weight: bold;
    font-size: 50%;
    padding-bottom: 1%;
}
.msg{
    font-size: 40%;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 3;
    overflow: hidden;
}
</style>