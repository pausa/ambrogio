import Vue from 'vue'
import App from './App.vue'

Vue.config.productionTip = false

var ipc = require("node-ipc");
ipc.config.id = 'ambrogio-ui';
ipc.config.retry = 1500;
ipc.serve(
    function () {
        ipc.server.on(
            'notification',
            function (data, sock) {
                ipc.log("hello workd");
                ipc.log(data);
                ipc.log(sock);
                this.socket = 'connected';
            }
        )
    }
);
ipc.server.start();

new Vue({
    render: h => h(App),
}).$mount('#app');