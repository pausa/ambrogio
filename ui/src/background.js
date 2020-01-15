const { app, BrowserWindow, protocol } = require('electron');
const express = require('express');
const bodyParser = require('body-parser');
const { createProtocol } = require('vue-cli-plugin-electron-builder/lib');

const isDevelopment = process.env.NODE_ENV === 'development';
let win;

function loadFront(win) {
  if (isDevelopment) {
    win.loadURL(process.env.WEBPACK_DEV_SERVER_URL);
  } else {
    createProtocol('app');
    win.loadFile('index.html');
  }
}

app.on('ready', () => {
  win = new BrowserWindow({
    width: 320,
    height: 240,
    kiosk: !isDevelopment,
    frame: false,
    webPreferences: {
      nodeIntegration: true
    }
  })
  loadFront(win);
});

const rest = express();
rest.use(bodyParser.urlencoded({ extended: false }));
rest.use(bodyParser.json());
// TODO find a way to do this without code duplication
rest.post('/notification', function (req, res) {
  let arg = {};
  arg.type = 'notification';
  arg.body = req.body;
  win.webContents.send('new-component', arg);
  res.sendStatus(200);
});
rest.post('/weather', function (req, res) {
  let arg = {};
  arg.type = 'weather';
  arg.body = req.body;
  win.webContents.send('new-component', arg);
  res.sendStatus(200);
});

rest.listen(3000);

