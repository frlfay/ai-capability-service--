/**
 * Creative Agent - AI 创意生成工作台
 * 参考 Lovart / TapNow 深色主题风格
 */

import { creativeGenerate } from '@/api/session'
import { useState, useRef, useCallback } from 'react'
import { Button, Input, message, Spin, Image, Tag } from 'antd'
import {
  PictureOutlined,
  VideoCameraOutlined,
  SendOutlined,
  LoadingOutlined,
  AppstoreOutlined,
  HighlightOutlined,
  PlaySquareOutlined,
  StarOutlined,
  StopOutlined,
} from '@ant-design/icons'
import styles from './index.module.scss'

const { TextArea } = Input

interface CreativeEvent {
  type: string
  [key: string]: any
}

interface GeneratedImage {
  url: string
  model: string
}

interface GeneratedVideo {
  url: string
  model: string
}

interface AgentStep {
  phase: string
  label: string
  status: 'pending' | 'running' | 'completed'
  detail?: string
}

const PRESET_PROMPTS = [
  { icon: <AppstoreOutlined />, label: 'Social Media', query: '帮我设计一个咖啡品牌的社交媒体海报，风格要温暖文艺，色调以棕色和奶白色为主' },
  { icon: <HighlightOutlined />, label: 'Logo & Branding', query: '为一个叫"星辰科技"的AI公司设计一个品牌Logo，风格要简约现代、科技感强' },
  { icon: <PictureOutlined />, label: 'Product Photo', query: '拍摄一双白色运动鞋的产品照片，背景简洁，光线专业，然后生成一段产品展示视频' },
  { icon: <PlaySquareOutlined />, label: 'Video Ad', query: '为一款新能源汽车制作一段视频广告，要有未来感和科技感，展示城市道路行驶' },
]

const PHASE_LABELS: Record<string, string> = {
  dispatching: 'Analyzed user intent',
  prompt_engineering: 'Optimized prompts',
  generating_image: 'Generating image',
  generating_video: 'Generating video',
  quality_checking: 'Quality inspection',
}

export default function CreativePage() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [steps, setSteps] = useState<AgentStep[]>([])
  const [images, setImages] = useState<GeneratedImage[]>([])
  const [videos, setVideos] = useState<GeneratedVideo[]>([])
  const [qualityScore, setQualityScore] = useState<number | null>(null)
  const [summary, setSummary] = useState('')
  const [started, setStarted] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const updateStep = useCallback((phase: string, status: 'running' | 'completed', detail?: string) => {
    setSteps((prev) => {
      const exists = prev.find((s) => s.phase === phase)
      if (exists) {
        return prev.map((s) =>
          s.phase === phase ? { ...s, status, detail: detail || s.detail } : s,
        )
      }
      return [
        ...prev.map((s) => (s.status === 'running' ? { ...s, status: 'completed' as const } : s)),
        { phase, label: PHASE_LABELS[phase] || phase, status, detail },
      ]
    })
  }, [])

  const handleGenerate = useCallback(async (inputQuery?: string) => {
    const q = inputQuery || query
    if (!q.trim()) {
      message.warning('Please enter your creative request')
      return
    }

    setStarted(true)
    setLoading(true)
    setSteps([])
    setImages([])
    setVideos([])
    setQualityScore(null)
    setSummary('')

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const res = await creativeGenerate({ query: q }, { signal: controller.signal })
      const stream = (res as any).data as ReadableStream
      const reader = stream?.getReader()
      if (!reader) throw new Error('No stream reader')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6).trim()
          if (data === '[DONE]') break

          try {
            const event: CreativeEvent = JSON.parse(data)
            const c = event.content ?? {}

            switch (event.type) {
              case 'phase':
                updateStep(c.phase, 'running', c.content)
                break
              case 'intent_parsed':
                updateStep('dispatching', 'completed', `${c.scene_name} / ${c.task_type}`)
                break
              case 'prompt_optimized':
                updateStep('prompt_engineering', 'completed', c.image_prompt?.slice(0, 80) + '...')
                break
              case 'image_generated':
                setImages((prev) => [...prev, { url: c.url, model: c.model }])
                updateStep('generating_image', 'completed')
                break
              case 'video_generated':
                setVideos((prev) => [...prev, { url: c.url, model: c.model }])
                updateStep('generating_video', 'completed')
                break
              case 'video_progress':
                updateStep('generating_video', 'running', `${c.status} (${c.elapsed_seconds}s)`)
                break
              case 'quality_result':
                setQualityScore(c.score)
                updateStep('quality_checking', 'completed', `Score: ${c.score}/10`)
                break
              case 'creative_complete':
                setSummary(event.final_output?.summary || 'Done')
                break
              case 'error': {
                const errMsg = typeof c === 'string' ? c : c?.content || JSON.stringify(c)
                message.error(errMsg)
                break
              }
            }
          } catch {
            // ignore
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        message.error(`Failed: ${err.message}`)
      }
    } finally {
      setLoading(false)
      abortRef.current = null
    }
  }, [query, updateStep])

  const handleCancel = useCallback(() => {
    abortRef.current?.abort()
    setLoading(false)
  }, [])

  const hasResults = images.length > 0 || videos.length > 0

  return (
    <div className={styles.page}>
      {/* 顶部导航 */}
      <div className={styles.navbar}>
        <div className={styles.brand}>
          <StarOutlined style={{ marginRight: 8 }} />
          Creative Agent
        </div>
        <div className={styles.navRight}>
          <Tag color="rgba(255,255,255,0.08)" style={{ color: 'rgba(255,255,255,0.4)', border: 'none', fontSize: 12 }}>
            5-Agent DAG
          </Tag>
        </div>
      </div>

      <div className={styles.main}>
        {/* 左侧画布区 */}
        <div className={styles.canvas}>
          {!started ? (
            <div className={styles.emptyState}>
              <h1>
                Design <strong>Creative Assets</strong> with AI Agents
              </h1>
              <p>Multi-agent collaboration for image and video generation</p>
              <div className={styles.skills}>
                {PRESET_PROMPTS.map((p) => (
                  <div
                    key={p.label}
                    className={styles.skillTag}
                    onClick={() => {
                      setQuery(p.query)
                      handleGenerate(p.query)
                    }}
                  >
                    {p.icon}
                    {p.label}
                  </div>
                ))}
              </div>
            </div>
          ) : hasResults ? (
            <div className={styles.resultArea}>
              <div className={styles.mediaGrid}>
                {images.map((img, i) => (
                  <div key={`img-${i}`} className={styles.mediaCard}>
                    <Image src={img.url} alt={`Image ${i + 1}`} width={380} style={{ borderRadius: 8 }} />
                    <div className={styles.mediaLabel}>
                      <span className={styles.mediaType}><PictureOutlined /> Image</span>
                      <span className={styles.modelTag}>{img.model}</span>
                    </div>
                  </div>
                ))}
                {videos.map((vid, i) => (
                  <div key={`vid-${i}`} className={styles.mediaCard}>
                    <video src={vid.url} controls width={380} style={{ borderRadius: 8 }} />
                    <div className={styles.mediaLabel}>
                      <span className={styles.mediaType}><VideoCameraOutlined /> Video</span>
                      <span className={styles.modelTag}>{vid.model}</span>
                    </div>
                  </div>
                ))}
              </div>
              {qualityScore !== null && (
                <div className={styles.scoreBadge}>
                  <span className={`${styles.scoreValue} ${qualityScore >= 7 ? styles.high : styles.low}`}>
                    {qualityScore.toFixed(1)}/10
                  </span>
                  <span>{summary}</span>
                </div>
              )}
            </div>
          ) : (
            <div className={styles.loadingCenter}>
              <Spin indicator={<LoadingOutlined style={{ fontSize: 32 }} spin />} />
              <span>Agents are working...</span>
            </div>
          )}
        </div>

        {/* 右侧面板 */}
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            {started ? 'Agent Workflow' : 'New Chat'}
          </div>

          <div className={styles.panelBody}>
            {!started && (
              <div style={{ color: 'rgba(255,255,255,0.3)', fontSize: 13, textAlign: 'center', marginTop: 40 }}>
                Try these skills, or describe your idea below
              </div>
            )}

            {steps.map((step) => (
              <div key={step.phase} className={`${styles.stepItem} ${styles[step.status]}`}>
                <div className={styles.stepDot} />
                <div className={styles.stepContent}>
                  <div className={styles.stepName}>{step.label}</div>
                  {step.detail && <div className={styles.stepDesc}>{step.detail}</div>}
                </div>
                {step.status === 'running' && (
                  <LoadingOutlined className={styles.stepSpinner} spin />
                )}
              </div>
            ))}
          </div>

          {/* 底部输入 */}
          <div className={styles.panelFooter}>
            <div className={styles.inputBox}>
              <TextArea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Describe your idea..."
                autoSize={{ minRows: 2, maxRows: 5 }}
                disabled={loading}
                onPressEnter={(e) => {
                  if (!e.shiftKey) {
                    e.preventDefault()
                    handleGenerate()
                  }
                }}
              />
              <div className={styles.inputActions}>
                <span className={styles.inputHint}>Enter to send</span>
                {loading ? (
                  <Button
                    type="text"
                    size="small"
                    icon={<StopOutlined />}
                    onClick={handleCancel}
                    style={{ color: 'rgba(255,255,255,0.4)' }}
                  />
                ) : (
                  <Button
                    type="primary"
                    size="small"
                    shape="circle"
                    icon={<SendOutlined />}
                    onClick={() => handleGenerate()}
                  />
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
