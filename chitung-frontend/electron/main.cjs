const { app, BrowserWindow, ipcMain, shell } = require('electron')
const { spawn } = require('node:child_process')
const fs = require('node:fs')
const path = require('node:path')

const isDev = process.env.VITE_DEV_SERVER_URL || process.env.NODE_ENV === 'development'
const serviceProcesses = []
let mainWindow = null

function getPreloadPath() {
  return path.join(__dirname, 'preload.cjs')
}

function getSuiteRoot() {
  if (app.isPackaged) {
    return process.resourcesPath
  }
  return path.resolve(__dirname, '..', '..')
}

function getLogDir() {
  const logDir = path.join(app.getPath('userData'), 'service-logs')
  fs.mkdirSync(logDir, { recursive: true })
  return logDir
}

async function isHealthy(url) {
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(1200) })
    return response.ok
  } catch {
    return false
  }
}

function spawnService(name, cwd, command, args) {
  const logPath = path.join(getLogDir(), `${name}.log`)
  const logStream = fs.createWriteStream(logPath, { flags: 'a' })
  const child = spawn(command, args, {
    cwd,
    env: { ...process.env },
    windowsHide: true,
    shell: false,
  })
  child.stdout.pipe(logStream)
  child.stderr.pipe(logStream)
  serviceProcesses.push(child)
}

function resolveVenvPython(projectDir) {
  const candidates = [
    path.join(projectDir, '.venv', 'bin', 'python'),
    path.join(projectDir, '.venv', 'Scripts', 'python.exe'),
  ]
  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) return candidate
  }
  return process.platform === 'win32' ? 'python' : 'python3'
}

async function startLocalServices() {
  if (process.env.CHITUNG_AUTOSTART_SERVICES === 'false') return

  const suiteRoot = getSuiteRoot()
  const centerDir = path.join(suiteRoot, 'chitung-center')
  const toolboxDir = path.join(suiteRoot, 'agent-toolbox')

  if (!(await isHealthy('http://127.0.0.1:8899/health'))) {
    spawnService('agent-toolbox', toolboxDir, resolveVenvPython(toolboxDir), ['run_server.py'])
  }

  if (!(await isHealthy('http://127.0.0.1:8999/health'))) {
    spawnService('chitung-center', centerDir, resolveVenvPython(centerDir), ['run_server.py'])
  }
}

function stopLocalServices() {
  for (const child of serviceProcesses) {
    if (!child.killed) child.kill()
  }
  serviceProcesses.length = 0
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 1180,
    minHeight: 760,
    title: '赤瞳安全智能平台',
    backgroundColor: '#f4f7fb',
    autoHideMenuBar: true,
    titleBarStyle: 'default',
    webPreferences: {
      preload: getPreloadPath(),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  })

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  if (isDev) {
    const devUrl = process.env.VITE_DEV_SERVER_URL || 'http://127.0.0.1:5173'
    mainWindow.loadURL(devUrl)
    return
  }

  mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
}

app.whenReady().then(() => {
  ipcMain.handle('app:get-runtime', () => ({
    platform: process.platform,
    version: app.getVersion(),
    centerUrl: process.env.CHITUNG_CENTER_URL || 'http://127.0.0.1:8999',
    logDir: getLogDir(),
  }))

  ipcMain.handle('file:open-path', async (_event, targetPath) => {
    if (!targetPath || typeof targetPath !== 'string') {
      return { ok: false, error: 'Invalid file path.' }
    }
    const error = await shell.openPath(targetPath)
    return { ok: !error, error }
  })

  ipcMain.handle('file:show-in-folder', (_event, targetPath) => {
    if (!targetPath || typeof targetPath !== 'string') {
      return { ok: false, error: 'Invalid file path.' }
    }
    shell.showItemInFolder(targetPath)
    return { ok: true }
  })

  ipcMain.handle('services:restart-local', async () => {
    stopLocalServices()
    await startLocalServices()
    return { ok: true, logDir: getLogDir() }
  })

  startLocalServices().finally(() => createMainWindow())

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    stopLocalServices()
    app.quit()
  }
})

app.on('before-quit', stopLocalServices)
