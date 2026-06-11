import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import '@/styles/variables.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import {
  Aim, ArrowLeft, Calendar, Check, Clock, Collection, Delete, Document,
  Edit, HomeFilled, Link, List, Lock, MagicStick, Message, Plus,
  RefreshRight, Search, Star, StarFilled, Timer, User, UserFilled,
  VideoPause, VideoPlay, Warning,
} from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

const app = createApp(App)

const icons = {
  Aim, ArrowLeft, Calendar, Check, Clock, Collection, Delete, Document,
  Edit, HomeFilled, Link, List, Lock, MagicStick, Message, Plus,
  RefreshRight, Search, Star, StarFilled, Timer, User, UserFilled,
  VideoPause, VideoPlay, Warning,
}
for (const [key, component] of Object.entries(icons)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
