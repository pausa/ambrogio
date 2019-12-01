const {app, BrowserWindow, ipcMain} = require('electron');
const express = require('express');
const bodyParser = require ('body-parser');

let url;
let win;
if (process.env.NODE_ENV === 'DEV') {
  url = 'http://localhost:8080/';
} else {
  console.log(process.cwd());
  url = `file://${process.cwd()}/dist/index.html`;
  url = 'http://localhost:5000/';
}

app.on('ready', () => {
  win = new BrowserWindow({
    width: 320, 
    height: 240,
    kiosk: true,
    frame: false,
    webPreferences: {
      nodeIntegration: true
    }
  })
  win.loadURL(url);
});

const rest = express();
rest.use(bodyParser.urlencoded({extended : false}));
rest.use(bodyParser.json());
rest.post('/notification', function(req, res){
  let arg = {};
  arg.type = 'notification';
  arg.body = req.body;
  win.webContents.send('new-component', arg);
  res.sendStatus(200);
});

rest.listen(3000);

