import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
//import vueJsx from '@vitejs/plugin-vue-jsx'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api/, '')
      }
    }
  }
})

// export default defineConfig({
//   plugins: [vue()],
//   server: {
//     proxy: {
//       '/tables': {
//         target: 'http://127.0.0.1:5000',
//         changeOrigin: true,
//         rewrite: path => path.replace(/^\/api/, '')
//       },
//       '/submit_statistics': {
//         target: 'http://127.0.0.1:5000',
//         changeOrigin: true,
//         rewrite: path => path.replace(/^\/api/, '')
//       }
//     }
//   }
// })