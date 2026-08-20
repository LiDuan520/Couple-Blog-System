/**
 * 相册 / 照片
 *
 * - 列表视图：相册网格（封面 + 照片数）
 * - 详情视图：瀑布流 + Lightbox
 * - 创建/编辑/删除相册
 * - 上传照片（拖拽 / 选择）
 * - 删除照片
 */
import { useState, useRef } from 'react'
import {
  Box, Card, CardBody, Heading, Text, HStack, VStack, Button, Tag,
  SimpleGrid, IconButton, useDisclosure, Modal, ModalOverlay, ModalContent,
  ModalHeader, ModalCloseButton, ModalBody, ModalFooter, FormControl,
  FormLabel, Input, Textarea, useToast, Image, Icon, Flex, Tooltip,
  Alert, AlertIcon, AspectRatio,
} from '@chakra-ui/react'
import {
  FiPlus, FiImage, FiTrash2, FiUpload, FiX, FiArrowLeft, FiEdit2,
} from 'react-icons/fi'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import PageContainer from '../../components/layout/PageContainer'
import { LoadingState, EmptyState } from '../../components/common/States'
import { albumApi } from '../../api/modules/album.api'
import { API_BASE_URL } from '../../utils/config'

function AlbumCard({ album, onOpen, onDelete }) {
  return (
    <Card overflow="hidden" cursor="pointer"
      _hover={{ transform: 'translateY(-4px)', boxShadow: '0 12px 40px rgba(0,0,0,0.15)' }}
      transition="all 0.2s" onClick={() => onOpen(album)}
    >
      <AspectRatio ratio={1}>
        <Box
          bg={album.cover_url ? 'transparent' :
            'linear-gradient(135deg, #FFE0EC 0%, #E6CCFF 100%)'}
        >
          {album.cover_url ? (
            <Image src={album.cover_url} alt={album.name} objectFit="cover" w="100%" h="100%" />
          ) : (
            <Flex align="center" justify="center" direction="column" color="brand.300">
              <Box fontSize="5xl">📷</Box>
              <Text fontSize="sm" fontWeight={600}>暂无照片</Text>
            </Flex>
          )}
        </Box>
      </AspectRatio>
      <CardBody>
        <HStack justify="space-between" align="flex-start">
          <Box flex={1} minW={0}>
            <Text fontWeight={700} noOfLines={1}>{album.name}</Text>
            <HStack mt={1}>
              <Tag size="sm" colorScheme="pink" borderRadius="full">
                {album.photo_count || 0} 张
              </Tag>
              {album.description && (
                <Text fontSize="xs" color="gray.500" noOfLines={1}>
                  {album.description}
                </Text>
              )}
            </HStack>
          </Box>
          <IconButton
            size="sm" variant="ghost" colorScheme="red" aria-label="del"
            icon={<FiTrash2 />}
            onClick={(e) => { e.stopPropagation(); onDelete(album) }}
          />
        </HStack>
      </CardBody>
    </Card>
  )
}

function AlbumDetailModal({ album, isOpen, onClose, onDelete }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const fileInput = useRef(null)
  const [lightbox, setLightbox] = useState(null)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['album-photos', album?.id],
    queryFn: () => albumApi.listPhotos(album.id),
    enabled: !!album?.id && isOpen,
  })
  const photos = data?.items || data?.data?.items || []

  const uploadMut = useMutation({
    mutationFn: (file) => {
      const fd = new FormData()
      fd.append('file', file)
      return albumApi.uploadPhoto(album.id, fd)
    },
    onSuccess: () => {
      toast({ status: 'success', title: '已上传' })
      queryClient.invalidateQueries({ queryKey: ['album-photos', album.id] })
      queryClient.invalidateQueries({ queryKey: ['albums'] })
    },
    onError: (err) => {
      toast({ status: 'error', title: '上传失败', description: err.message })
    },
  })

  const delPhotoMut = useMutation({
    mutationFn: (photoId) => albumApi.removePhoto(photoId),
    onSuccess: () => {
      toast({ status: 'success', title: '已删除' })
      queryClient.invalidateQueries({ queryKey: ['album-photos', album.id] })
      queryClient.invalidateQueries({ queryKey: ['albums'] })
    },
  })

  if (!album) return null
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="4xl" isCentered>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>
          <HStack>
            <Icon as={FiImage} color="brand.500" />
            <Text>{album.name}</Text>
            <Tag size="sm" colorScheme="pink" borderRadius="full">
              {photos.length} 张
            </Tag>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <input
            type="file" ref={fileInput} style={{ display: 'none' }}
            accept="image/*" multiple
            onChange={(e) => {
              Array.from(e.target.files || []).forEach((f) => uploadMut.mutate(f))
              e.target.value = ''
            }}
          />
          <Button size="sm" leftIcon={<FiUpload />} colorScheme="brand"
            mb={4}
            isLoading={uploadMut.isPending}
            onClick={() => fileInput.current?.click()}>
            上传照片
          </Button>

          {isLoading ? (
            <LoadingState />
          ) : photos.length === 0 ? (
            <EmptyState icon="🖼️" title="还没有照片"
              description="上传第一张属于你们的照片吧" />
          ) : (
            <SimpleGrid columns={{ base: 2, md: 3, lg: 4 }} spacing={3}>
              {photos.map((p) => (
                <Box key={p.id} position="relative" borderRadius="xl" overflow="hidden"
                  cursor="pointer" onClick={() => setLightbox(p)}>
                  <AspectRatio ratio={1}>
                    <Image src={p.url} alt={p.caption || ''} objectFit="cover" />
                  </AspectRatio>
                  <IconButton
                    position="absolute" top={2} right={2} size="xs"
                    icon={<FiX />} colorScheme="blackAlpha" aria-label="del"
                    onClick={(e) => {
                      e.stopPropagation()
                      if (window.confirm('删除这张照片？')) delPhotoMut.mutate(p.id)
                    }}
                  />
                </Box>
              ))}
            </SimpleGrid>
          )}
        </ModalBody>
      </ModalContent>

      {/* Lightbox */}
      {lightbox && (
        <Modal isOpen={!!lightbox} onClose={() => setLightbox(null)} size="full" isCentered>
          <ModalOverlay bg="blackAlpha.900" />
          <ModalContent bg="transparent" boxShadow="none" maxW="100vw">
            <ModalCloseButton color="white" size="lg" />
            <ModalBody display="flex" alignItems="center" justifyContent="center"
              minH="100vh" p={4}>
              <Image src={lightbox.url} alt="" maxH="90vh" maxW="90vw"
                objectFit="contain" borderRadius="lg" />
            </ModalBody>
          </ModalContent>
        </Modal>
      )}
    </Modal>
  )
}

function AlbumFormModal({ isOpen, onClose }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const toast = useToast()
  const queryClient = useQueryClient()
  const createMut = useMutation({
    mutationFn: () => albumApi.create({ name, description }),
    onSuccess: () => {
      toast({ status: 'success', title: '已创建' })
      queryClient.invalidateQueries({ queryKey: ['albums'] })
      onClose()
      setName(''); setDescription('')
    },
  })
  return (
    <Modal isOpen={isOpen} onClose={onClose} isCentered>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>新建相册</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={4}>
            <FormControl isRequired>
              <FormLabel>相册名</FormLabel>
              <Input value={name} onChange={(e) => setName(e.target.value)}
                placeholder="如：第一次旅行" />
            </FormControl>
            <FormControl>
              <FormLabel>描述</FormLabel>
              <Textarea value={description} onChange={(e) => setDescription(e.target.value)}
                rows={2} placeholder="选填" />
            </FormControl>
          </VStack>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" mr={2} onClick={onClose}>取消</Button>
          <Button colorScheme="brand" isDisabled={!name}
            isLoading={createMut.isPending} onClick={() => createMut.mutate()}>
            创建
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  )
}

export default function Albums() {
  const [opened, setOpened] = useState(null)
  const newDisc = useDisclosure()
  const toast = useToast()
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['albums'],
    queryFn: () => albumApi.list(),
  })
  const albums = data?.items || data?.data?.items || []

  const delMut = useMutation({
    mutationFn: (id) => albumApi.remove(id),
    onSuccess: () => {
      toast({ status: 'success', title: '已删除' })
      queryClient.invalidateQueries({ queryKey: ['albums'] })
    },
  })

  return (
    <PageContainer
      title="相册 📷"
      subtitle="珍藏每一帧甜蜜"
      actions={
        <Button colorScheme="brand" leftIcon={<FiPlus />}
          onClick={newDisc.onOpen}>
          新建相册
        </Button>
      }
    >
      {isLoading ? (
        <LoadingState />
      ) : albums.length === 0 ? (
        <EmptyState
          icon="📷"
          title="还没有相册"
          description="创建一个相册，开始上传照片吧"
          actionLabel="创建相册"
          onAction={newDisc.onOpen}
        />
      ) : (
        <SimpleGrid columns={{ base: 2, md: 3, lg: 4 }} spacing={4}>
          {albums.map((a) => (
            <AlbumCard
              key={a.id}
              album={a}
              onOpen={setOpened}
              onDelete={(it) => {
                if (window.confirm(`删除相册「${it.name}」？所有照片也会被删除`)) {
                  delMut.mutate(it.id)
                }
              }}
            />
          ))}
        </SimpleGrid>
      )}

      <AlbumFormModal isOpen={newDisc.isOpen} onClose={newDisc.onClose} />
      <AlbumDetailModal
        album={opened}
        isOpen={!!opened}
        onClose={() => setOpened(null)}
        onDelete={() => {}}
      />
    </PageContainer>
  )
}
