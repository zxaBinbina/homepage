import { createApp, nextTick } from 'vue'
import App from './App.vue'
import { router } from './router'
import './style.css'
import { finishInitialLoading, failInitialLoading, waitForInitialStyles } from './loading/state'
const app = createApp(App).use(router)
Promise.all([router.isReady(), waitForInitialStyles()])
  .then(async () => {
    app.mount('#app')
    await nextTick()
    finishInitialLoading()
  })
  .catch(failInitialLoading)
