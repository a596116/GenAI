import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import dts from 'vite-plugin-dts'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // 判斷是否構建獨立版本（包含 Vue）
  const isStandalone = mode === 'standalone'

  return {
    define: {
      'process.env.NODE_ENV': JSON.stringify(
        mode === 'production' ? 'production' : 'development'
      ),
    },
    plugins: [
      vue(),
      dts({
        insertTypesEntry: true,
        rollupTypes: true,
      }),
    ],
    build: {
      // 使用 emptyOutDir: false 來避免清空輸出目錄
      emptyOutDir: !isStandalone,
      lib: {
        entry: isStandalone
          ? resolve(__dirname, 'src/standalone.ts')
          : resolve(__dirname, 'src/index.ts'),
        name: 'HaoChatbot',
        formats: isStandalone ? ['umd'] : ['es', 'cjs'],
        fileName: (format) =>
          isStandalone ? `index.standalone.${format}.js` : `index.${format}.js`,
      },
      rollupOptions: {
        // 獨立版本不 externalize Vue，把 Vue 打包進去
        external: isStandalone ? [] : ['vue'],
        output: {
          // 在 UMD 構建模式下為這些外部化的依賴提供一個全局變量
          globals: isStandalone
            ? {}
            : {
                vue: 'Vue',
              },
          // 導出 CSS
          assetFileNames: (assetInfo) => {
            if (assetInfo.name === 'style.css') return 'style.css'
            return assetInfo.name as string
          },
        },
      },
    },
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
      },
    },
    css: {
      preprocessorOptions: {
        scss: {
          api: 'modern-compiler',
        },
      },
    },
  }
})
