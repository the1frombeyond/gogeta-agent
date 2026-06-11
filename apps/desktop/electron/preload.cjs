const { contextBridge, ipcRenderer, webUtils } = require('electron')

contextBridge.exposeInMainWorld('gogetaDesktop', {
  getConnection: profile => ipcRenderer.invoke('gogeta:connection', profile),
  touchBackend: profile => ipcRenderer.invoke('gogeta:backend:touch', profile),
  getGatewayWsUrl: profile => ipcRenderer.invoke('gogeta:gateway:ws-url', profile),
  getBootProgress: () => ipcRenderer.invoke('gogeta:boot-progress:get'),
  getConnectionConfig: profile => ipcRenderer.invoke('gogeta:connection-config:get', profile),
  saveConnectionConfig: payload => ipcRenderer.invoke('gogeta:connection-config:save', payload),
  applyConnectionConfig: payload => ipcRenderer.invoke('gogeta:connection-config:apply', payload),
  testConnectionConfig: payload => ipcRenderer.invoke('gogeta:connection-config:test', payload),
  probeConnectionConfig: remoteUrl => ipcRenderer.invoke('gogeta:connection-config:probe', remoteUrl),
  oauthLoginConnectionConfig: remoteUrl => ipcRenderer.invoke('gogeta:connection-config:oauth-login', remoteUrl),
  oauthLogoutConnectionConfig: remoteUrl => ipcRenderer.invoke('gogeta:connection-config:oauth-logout', remoteUrl),
  profile: {
    get: () => ipcRenderer.invoke('gogeta:profile:get'),
    set: name => ipcRenderer.invoke('gogeta:profile:set', name)
  },
  api: request => ipcRenderer.invoke('gogeta:api', request),
  notify: payload => ipcRenderer.invoke('gogeta:notify', payload),
  requestMicrophoneAccess: () => ipcRenderer.invoke('gogeta:requestMicrophoneAccess'),
  readFileDataUrl: filePath => ipcRenderer.invoke('gogeta:readFileDataUrl', filePath),
  readFileText: filePath => ipcRenderer.invoke('gogeta:readFileText', filePath),
  selectPaths: options => ipcRenderer.invoke('gogeta:selectPaths', options),
  writeClipboard: text => ipcRenderer.invoke('gogeta:writeClipboard', text),
  saveImageFromUrl: url => ipcRenderer.invoke('gogeta:saveImageFromUrl', url),
  saveImageBuffer: (data, ext) => ipcRenderer.invoke('gogeta:saveImageBuffer', { data, ext }),
  saveClipboardImage: () => ipcRenderer.invoke('gogeta:saveClipboardImage'),
  getPathForFile: file => {
    try {
      return webUtils.getPathForFile(file) || ''
    } catch {
      return ''
    }
  },
  normalizePreviewTarget: (target, baseDir) => ipcRenderer.invoke('gogeta:normalizePreviewTarget', target, baseDir),
  watchPreviewFile: url => ipcRenderer.invoke('gogeta:watchPreviewFile', url),
  stopPreviewFileWatch: id => ipcRenderer.invoke('gogeta:stopPreviewFileWatch', id),
  setTitleBarTheme: payload => ipcRenderer.send('gogeta:titlebar-theme', payload),
  setPreviewShortcutActive: active => ipcRenderer.send('gogeta:previewShortcutActive', Boolean(active)),
  openExternal: url => ipcRenderer.invoke('gogeta:openExternal', url),
  fetchLinkTitle: url => ipcRenderer.invoke('gogeta:fetchLinkTitle', url),
  settings: {
    getDefaultProjectDir: () => ipcRenderer.invoke('gogeta:setting:defaultProjectDir:get'),
    setDefaultProjectDir: dir => ipcRenderer.invoke('gogeta:setting:defaultProjectDir:set', dir),
    pickDefaultProjectDir: () => ipcRenderer.invoke('gogeta:setting:defaultProjectDir:pick')
  },
  revealLogs: () => ipcRenderer.invoke('gogeta:logs:reveal'),
  getRecentLogs: () => ipcRenderer.invoke('gogeta:logs:recent'),
  readDir: dirPath => ipcRenderer.invoke('gogeta:fs:readDir', dirPath),
  gitRoot: startPath => ipcRenderer.invoke('gogeta:fs:gitRoot', startPath),
  terminal: {
    dispose: id => ipcRenderer.invoke('gogeta:terminal:dispose', id),
    resize: (id, size) => ipcRenderer.invoke('gogeta:terminal:resize', id, size),
    start: options => ipcRenderer.invoke('gogeta:terminal:start', options),
    write: (id, data) => ipcRenderer.invoke('gogeta:terminal:write', id, data),
    onData: (id, callback) => {
      const channel = `gogeta:terminal:${id}:data`
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on(channel, listener)
      return () => ipcRenderer.removeListener(channel, listener)
    },
    onExit: (id, callback) => {
      const channel = `gogeta:terminal:${id}:exit`
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on(channel, listener)
      return () => ipcRenderer.removeListener(channel, listener)
    }
  },
  onClosePreviewRequested: callback => {
    const listener = () => callback()
    ipcRenderer.on('gogeta:close-preview-requested', listener)
    return () => ipcRenderer.removeListener('gogeta:close-preview-requested', listener)
  },
  onOpenUpdatesRequested: callback => {
    const listener = () => callback()
    ipcRenderer.on('gogeta:open-updates', listener)
    return () => ipcRenderer.removeListener('gogeta:open-updates', listener)
  },
  onWindowStateChanged: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('gogeta:window-state-changed', listener)
    return () => ipcRenderer.removeListener('gogeta:window-state-changed', listener)
  },
  onPreviewFileChanged: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('gogeta:preview-file-changed', listener)
    return () => ipcRenderer.removeListener('gogeta:preview-file-changed', listener)
  },
  onBackendExit: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('gogeta:backend-exit', listener)
    return () => ipcRenderer.removeListener('gogeta:backend-exit', listener)
  },
  onPowerResume: callback => {
    const listener = () => callback()
    ipcRenderer.on('gogeta:power-resume', listener)
    return () => ipcRenderer.removeListener('gogeta:power-resume', listener)
  },
  onBootProgress: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('gogeta:boot-progress', listener)
    return () => ipcRenderer.removeListener('gogeta:boot-progress', listener)
  },
  // First-launch bootstrap progress -- emitted by the install.ps1 stage
  // runner in main.cjs (apps/desktop/electron/bootstrap-runner.cjs).
  // Renderer's install overlay subscribes to live events and queries the
  // current snapshot via getBootstrapState() to recover after a devtools
  // reload mid-bootstrap.
  getBootstrapState: () => ipcRenderer.invoke('gogeta:bootstrap:get'),
  resetBootstrap: () => ipcRenderer.invoke('gogeta:bootstrap:reset'),
  repairBootstrap: () => ipcRenderer.invoke('gogeta:bootstrap:repair'),
  cancelBootstrap: () => ipcRenderer.invoke('gogeta:bootstrap:cancel'),
  onBootstrapEvent: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('gogeta:bootstrap:event', listener)
    return () => ipcRenderer.removeListener('gogeta:bootstrap:event', listener)
  },
  getVersion: () => ipcRenderer.invoke('gogeta:version'),
  uninstall: {
    summary: () => ipcRenderer.invoke('gogeta:uninstall:summary'),
    run: mode => ipcRenderer.invoke('gogeta:uninstall:run', { mode })
  },
  updates: {
    check: () => ipcRenderer.invoke('gogeta:updates:check'),
    apply: opts => ipcRenderer.invoke('gogeta:updates:apply', opts),
    getBranch: () => ipcRenderer.invoke('gogeta:updates:branch:get'),
    setBranch: name => ipcRenderer.invoke('gogeta:updates:branch:set', name),
    onProgress: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('gogeta:updates:progress', listener)
      return () => ipcRenderer.removeListener('gogeta:updates:progress', listener)
    }
  }
})
