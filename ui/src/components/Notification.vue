<template>
  <div id = "notification">
    <p class="title">{{ title }}</p>
    <p class="msg">{{ msg }}</p>
  </div>
</template>
<script>
export default {
    props: ['title', 'msg']
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