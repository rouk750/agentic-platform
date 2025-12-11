import { app, BrowserWindow, ipcMain } from 'electron'
import { join } from 'node:path'
import { spawn, ChildProcess } from 'node:child_process'
import path from 'node:path'

process.env.DIST = join(__dirname, '../dist')
process.env.VITE_PUBLIC = app.isPackaged ? process.env.DIST : join(process.env.DIST, '../public')

let win: BrowserWindow | null
// 🚧 Use ['ENV_NAME'] avoid vite:define plugin - Vite@2.x
const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL']

let pythonProcess: ChildProcess | null = null
let apiPort: number = 0

async function startPythonBackend() {
  // Dynamic import for ESM module
  // const getPort = (await import('get-port')).default
  // apiPort = await getPort()
  apiPort = 8000 
  
  console.log('Starting Python backend on port', apiPort)
  
  if (!app.isPackaged) {
     // Dev Mode
     // Root of repo is likely 2 levels up from dist-electron (frontend/dist-electron)
     // But __dirname points to dist-electron/main.js
     // frontend is __dirname/../.. ? No.
     // dist-electron lies in frontend/
     // So __dirname is .../frontend/dist-electron
     // backend is .../frontend/../backend
     
     const backendPath = path.resolve(__dirname, '../../backend')
     console.log('Backend path:', backendPath)

     // Spawn poetry
     pythonProcess = spawn('poetry', ['run', 'start', '--port', apiPort.toString()], {
        cwd: backendPath,
        shell: true,
     })
  } else {
    // Prod implementation placeholder
  }

  if (pythonProcess) {
      pythonProcess.stdout?.on('data', (data) => {
        const log = `[Python]: ${data}`
        console.log(log)
        // Send to renderer for debug
        win?.webContents.send('python-log', log)
      })
      pythonProcess.stderr?.on('data', (data) => {
        const log = `[Python Error]: ${data}`
        console.error(log)
        win?.webContents.send('python-log', log)
      })
      pythonProcess.on('close', (code) => {
        console.log(`Python process exited with code ${code}`)
      })
  }
}

function createWindow() {
  win = new BrowserWindow({
    width: 1280,
    height: 800,
    icon: path.join(process.env.VITE_PUBLIC, 'electron-vite.svg'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  })

  win.webContents.on('did-finish-load', () => {
    win?.webContents.send('init-api-port', apiPort)
  })

  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL)
  } else {
    win.loadFile(path.join(process.env.DIST, 'index.html'))
  }
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
    win = null
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

app.on('will-quit', () => {
    if (pythonProcess) {
        pythonProcess.kill()
    }
})

app.whenReady().then(async () => {
    await startPythonBackend()
    createWindow()
})

ipcMain.handle('get-api-port', () => {
    return apiPort
})
