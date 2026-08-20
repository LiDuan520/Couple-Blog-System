/**
 * 博客列表 - 粉紫少女风
 */
import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box, Card, CardBody, Heading, Text, HStack, VStack, Button, Tag,
  Input, InputGroup, InputLeftElement, IconButton, Wrap, WrapItem,
  useToast, SimpleGrid, Avatar, Flex, Icon,
} from '@chakra-ui/react'
import { FiSearch, FiPlus, FiEdit2, FiTrash2, FiEye, FiBookOpen } from 'react-icons/fi'
import dayjs from 'dayjs'
import PageContainer from '../../components/layout/PageContainer'
import { LoadingState, EmptyState } from '../../components/common/States'
import { blogAPI } from '../../api/modules/blog.api'
import { useAuthStore } from '../../store/authStore'

function BlogCard({ blog, onOpen, onEdit, onDelete, canEdit }) {
  return (
    <Card
      cursor="pointer" onClick={onOpen}
      _hover={{ transform: 'translateY(-4px)', boxShadow: '0 12px 32px rgba(196,69,105,0.15)' }}
      transition="all 0.2s" h="full"
    >
      <CardBody>
        <HStack mb={2} align="flex-start">
          <Box flex={1} minW={0}>
            <HStack mb={1}>
              {blog.is_public && (
                <Tag size="sm" colorScheme="green" borderRadius="full">公开</Tag>
              )}
              {blog.couple_id && (
                <Tag size="sm" colorScheme="pink" borderRadius="full">💕 情侣</Tag>
              )}
            </HStack>
            <Heading size="md" noOfLines={1}>{blog.title}</Heading>
          </Box>
          {canEdit && (
            <HStack spacing={1} onClick={(e) => e.stopPropagation()}>
              <IconButton size="sm" variant="ghost" icon={<FiEdit2 />}
                aria-label="edit" onClick={onEdit} />
              <IconButton size="sm" variant="ghost" colorScheme="red"
                icon={<FiTrash2 />} aria-label="delete" onClick={onDelete} />
            </HStack>
          )}
        </HStack>
        <Text color="gray.600" fontSize="sm" noOfLines={3} minH="60px">
          {blog.content}
        </Text>
        {blog.tags?.length > 0 && (
          <Wrap mt={3} spacing={2}>
            {blog.tags.map((t) => (
              <WrapItem key={t}>
                <Tag size="sm" variant="subtle" colorScheme="pink">#{t}</Tag>
              </WrapItem>
            ))}
          </Wrap>
        )}
        <HStack mt={3} fontSize="xs" color="gray.400" justify="space-between">
          <Text>{dayjs(blog.created_at).format('YYYY-MM-DD')}</Text>
          <Text>{blog.content.length} 字</Text>
        </HStack>
      </CardBody>
    </Card>
  )
}

export default function BlogList() {
  const navigate = useNavigate()
  const toast = useToast()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 12

  const { data, isLoading } = useQuery({
    queryKey: ['blogs', { search, page, pageSize }],
    queryFn: () => blogAPI.getBlogs({ search, page, page_size: pageSize }),
  })
  const payload = data?.data || data
  const items = payload?.items || []
  const totalPages = payload?.total_pages || 1

  const delMut = useMutation({
    mutationFn: (id) => blogAPI.deleteBlog(id),
    onSuccess: () => {
      toast({ status: 'success', title: '已删除' })
      queryClient.invalidateQueries({ queryKey: ['blogs'] })
    },
  })

  return (
    <PageContainer
      title="博客 ✍️"
      subtitle={user?.couple ? '你们共同的记录' : '我的记录'}
      actions={
        <Button as={Link} to="/blogs/new" colorScheme="brand" leftIcon={<FiPlus />}>
          写博客
        </Button>
      }
    >
      <InputGroup mb={6} maxW="md">
        <InputLeftElement><FiSearch color="#999" /></InputLeftElement>
        <Input
          placeholder="搜索标题或内容"
          value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          bg="white"
        />
      </InputGroup>

      {isLoading ? (
        <LoadingState />
      ) : items.length === 0 ? (
        <EmptyState
          icon="📓"
          title="还没有博客"
          description="写第一篇记录吧"
          actionLabel="开始写"
          onAction={() => navigate('/blogs/new')}
        />
      ) : (
        <>
          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={5}>
            {items.map((b) => (
              <BlogCard
                key={b.id} blog={b}
                onOpen={() => navigate(`/blogs/${b.id}`)}
                onEdit={() => navigate(`/blogs/${b.id}/edit`)}
                onDelete={() => {
                  if (window.confirm(`删除「${b.title}」？`)) delMut.mutate(b.id)
                }}
                canEdit={b.author_id === user?.id}
              />
            ))}
          </SimpleGrid>

          {totalPages > 1 && (
            <HStack justify="center" mt={6} spacing={2}>
              <Button size="sm" isDisabled={page <= 1}
                onClick={() => setPage(page - 1)}>上一页</Button>
              <Text fontSize="sm" color="gray.500">{page} / {totalPages}</Text>
              <Button size="sm" isDisabled={page >= totalPages}
                onClick={() => setPage(page + 1)}>下一页</Button>
            </HStack>
          )}
        </>
      )}
    </PageContainer>
  )
}
