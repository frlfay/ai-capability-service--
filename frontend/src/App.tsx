import { Router } from '@/router'
import { App as AntdApp, ConfigProvider, theme } from 'antd'

function App() {
  return (
    <ConfigProvider
      theme={{
        cssVar: true,
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: '#fff',
          colorBgContainer: '#1a1a1a',
          borderRadius: 8,
        },
      }}
    >
      <AntdApp>
        <Router />
      </AntdApp>
    </ConfigProvider>
  )
}

export default App
