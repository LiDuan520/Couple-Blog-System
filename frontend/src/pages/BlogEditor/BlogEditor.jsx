/**
 * 博客编辑器 - 粉紫少女风
 */
import { useState, useEffect } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box, Card, CardBody, Heading, Text, HStack, VStack, Button, Tag,
  Input, Textarea, Switch, FormControl, FormLabel, Wrap, WrapItem,
  TagLabel, TagCloseButton, useToast, IconButton, Flex, Alert, AlertIcon,
} from '@chakra-ui/react'
import { FiEye, FiEdit3, FiSave, FiX, FiArrowLeft } from 'react-icons/fi'
import PageContainer from '../../components/layout/PageContainer'
import { LoadingState } from '../../components/common/States'
import { blogAPI } from '../../api/modules/blog.api'
import { MarkdownView } from '../../utils/markdown'

const EMPTY_DRAFT = { title: '', content: '', tags: [], is_public: false }

function BlogEditor() {
  const { id } = useParams()
  const isEdit = !!id
  const navigate = useNavigate()
  const toast = useToast()
  const queryClient = useQueryClient()

  const [form, setForm] = useState(EMPTY_DRAFT)
  const [tagInput, setTagInput] = useState('')
  const [showPreview, setShowPreview] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  const { data: existing, isLoading } = useQuery({
    queryKey: ['blog', id],
    queryFn: async () => {
      const res = await blogAPI.getBlog(id)
      return res.data || res
    },
    enabled: isEdit,
  })

  useEffect(() => {
    if (existing) {
      setForm({
        title: existing.title || '',
        content: existing.content || '',
        tags: existing.tags || [],
        is_public: !!existing.is_public,
      })
    }
  }, [existing])

  const saveMutation = useMutation({
    mutationFn: async (payload) => {
      if (isEdit) return blogAPI.updateBlog(id, payload)
      return blogAPI.createBlog(payload)
    },
    onSuccess: (res) => {
      toast({ status: 'success', title: isEdit ? '已更新' : '已发布' })
      queryClient.invalidateQueries({ queryKey: ['blogs'] })
      const data = res.data || res
      navigate(`/blogs/${data.id}`)
    },
    onError: (err) => {
      toast({ status: 'error', title: '保存失败', description: err.message })
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    setErrorMsg('')
    if (!form.title.trim()) { setErrorMsg('标题不能为空'); return }
    if (!form.content.trim()) { setErrorMsg('内容不能为空'); return }
    if (form.title.length > 200) { setErrorMsg('标题不能超过 200 字'); return }
    if (form.content.length > 10000) { setErrorMsg('内容不能超过 10000 字'); return }
    saveMutation.mutate(form)
  }

  const addTag = () => {
    const t = tagInput.trim()
    if (!t) return
    if (t.length > 20) { setErrorMsg('单个标签最多 20 字'); return }
    if (form.tags.length >= 10) { setErrorMsg('最多 10 个标签'); return }
    if (!form.tags.includes(t)) {
      setForm((p) => ({ ...p, tags: [...p.tags, t] }))
    }
    setTagInput('')
  }
  const removeTag = (t) => setForm((p) => ({ ...p, tags: p.tags.filter((x) => x !== t) }))

  if (isEdit && isLoading) return <LoadingState />

  return (
    <PageContainer
      title={isEdit ? '编辑博客 ✏️' : '写新博客 ✍️'}
      actions={
        <Button as={Link} to="/blogs" variant="ghost" leftIcon={<FiArrowLeft />}>
          返回
        </Button>
      }
    >
      <Card>
        <CardBody>
          <form onSubmit={handleSubmit}>
            <VStack spacing={5} align="stretch">
              <FormControl>
                <FormLabel>标题</FormLabel>
                <Input
                  value={form.title}
                  onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))}
                  maxLength={200}
                  placeholder="给你的博客起个名字…"
                  fontSize="lg" fontWeight={600}
                />
                <Text fontSize="xs" color="gray.400" textAlign="right" mt={1}>
                  {form.title.length} / 200
                </Text>
              </FormControl>

              <FormControl>
                <HStack justify="space-between" mb={2}>
                  <FormLabel mb={0}>内容（支持 Markdown）</FormLabel>
                  <Button size="xs" variant="ghost" leftIcon={showPreview ? <FiEdit3 /> : <FiEye />}
                    onClick={() => setShowPreview((v) => !v)}>
                    {showPreview ? '编辑' : '预览'}
                  </Button>
                </HStack>
                {showPreview ? (
                  <Box minH="320px" p={4} borderWidth="1px" borderRadius="md"
                    borderColor="brand.100" bg="brand.50">
                    <MarkdownView source={form.content || '（暂无内容）'} />
                  </Box>
                ) : (
                  <Textarea
                    value={form.content}
                    onChange={(e) => setForm((p) => ({ ...p, content: e.target.value }))}
                    minH="320px" fontFamily="Menlo, Consolas, monospace"
                    fontSize="sm" resize="vertical"
                    maxLength={10000}
                    placeholder="# 标题&#10;&#10;用 Markdown 写下你的故事…"
                  />
                )}
                <Text fontSize="xs" color="gray.400" textAlign="right" mt={1}>
                  {form.content.length} / 10000
                </Text>
              </FormControl>

              <FormControl>
                <FormLabel>标签</FormLabel>
                <Wrap spacing={2} mb={2}>
                  {form.tags.map((t) => (
                    <WrapItem key={t}>
                      <Tag size="md" colorScheme="pink" borderRadius="full">
                        <TagLabel>#{t}</TagLabel>
                        <TagCloseButton onClick={() => removeTag(t)} />
                      </Tag>
                    </WrapItem>
                  ))}
                </Wrap>
                <HStack>
                  <Input
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                    placeholder="输入标签后回车" maxLength={20}
                  />
                  <Button onClick={addTag} variant="outline" colorScheme="brand">
                    添加
                  </Button>
                </HStack>
              </FormControl>

              <FormControl display="flex" alignItems="center">
                <FormLabel mb={0}>公开（其他用户可查看）</FormLabel>
                <Switch
                  isChecked={form.is_public}
                  onChange={(e) => setForm((p) => ({ ...p, is_public: e.target.checked }))}
                  colorScheme="pink"
                />
              </FormControl>

              {errorMsg && (
                <Alert status="warning" borderRadius="md">
                  <AlertIcon />
                  {errorMsg}
                </Alert>
              )}

              <HStack>
                <Button type="submit" colorScheme="brand" flex={1}
                  isLoading={saveMutation.isLoading} leftIcon={<FiSave />}>
                  {isEdit ? '更新' : '发布'}
                </Button>
                <Button variant="ghost" flex={1} onClick={() => navigate('/blogs')}>
                  取消
                </Button>
              </HStack>
            </VStack>
          </form>
        </CardBody>
      </Card>
    </PageContainer>
  )
}

export default BlogEditor
