/**
 * 博客详情 - 粉紫少女风
 */
import { useNavigate, useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box, Card, CardBody, Heading, Text, HStack, VStack, Button, Tag,
  Wrap, WrapItem, useToast, Divider, IconButton,
} from '@chakra-ui/react'
import { FiArrowLeft, FiEdit2, FiTrash2 } from 'react-icons/fi'
import dayjs from 'dayjs'
import PageContainer from '../../components/layout/PageContainer'
import { LoadingState, EmptyState } from '../../components/common/States'
import { blogAPI } from '../../api/modules/blog.api'
import { useAuthStore } from '../../store/authStore'
import { MarkdownView } from '../../utils/markdown'

function BlogDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()

  const { data: blog, isLoading, isError } = useQuery({
    queryKey: ['blog', id],
    queryFn: async () => {
      const res = await blogAPI.getBlog(id)
      return res.data || res
    },
    enabled: !!id,
  })

  const deleteMutation = useMutation({
    mutationFn: () => blogAPI.deleteBlog(id),
    onSuccess: () => {
      toast({ status: 'success', title: '已删除' })
      queryClient.invalidateQueries({ queryKey: ['blogs'] })
      navigate('/blogs')
    },
  })

  if (isLoading) return <LoadingState />
  if (isError) return (
    <EmptyState icon="😅" title="加载失败"
      actionLabel="返回列表" onAction={() => navigate('/blogs')} />
  )
  if (!blog) return null

  const canEdit = blog.author_id === user?.id

  return (
    <PageContainer
      maxW="3xl"
      actions={
        <HStack>
          <Button as={Link} to="/blogs" variant="ghost" leftIcon={<FiArrowLeft />}>
            返回
          </Button>
          {canEdit && (
            <>
              <Button leftIcon={<FiEdit2 />} colorScheme="brand" variant="outline"
                onClick={() => navigate(`/blogs/${id}/edit`)}>
                编辑
              </Button>
              <Button leftIcon={<FiTrash2 />} colorScheme="red"
                onClick={() => {
                  if (window.confirm('确定要删除这篇博客吗？')) deleteMutation.mutate()
                }}
                isLoading={deleteMutation.isPending}>
                删除
              </Button>
            </>
          )}
        </HStack>
      }
    >
      <Card>
        <CardBody>
          <HStack mb={3} flexWrap="wrap">
            {blog.is_public && (
              <Tag size="sm" colorScheme="green" borderRadius="full">公开</Tag>
            )}
            {blog.couple_id && (
              <Tag size="sm" colorScheme="pink" borderRadius="full">💕 情侣</Tag>
            )}
            <Text fontSize="sm" color="gray.500" ml="auto">
              {dayjs(blog.created_at).format('YYYY-MM-DD HH:mm')}
            </Text>
          </HStack>

          <Heading size="xl" mb={4}
            bgGradient="linear(to-r, brand.500, purple.500)" bgClip="text">
            {blog.title}
          </Heading>

          {blog.tags?.length > 0 && (
            <Wrap mb={4} spacing={2}>
              {blog.tags.map((t) => (
                <WrapItem key={t}>
                  <Tag size="sm" colorScheme="pink" variant="subtle">#{t}</Tag>
                </WrapItem>
              ))}
            </Wrap>
          )}

          <Divider mb={6} borderColor="brand.100" />

          <Box className="markdown-body">
            <MarkdownView source={blog.content} />
          </Box>
        </CardBody>
      </Card>
    </PageContainer>
  )
}

export default BlogDetail
