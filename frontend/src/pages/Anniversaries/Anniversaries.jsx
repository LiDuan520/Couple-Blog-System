/**
 * 纪念日
 *
 * - 列表卡片（按日期排序）
 * - 倒计时数字
 * - 创建/编辑/删除（Modal）
 * - 重复/不重复切换
 */
import { useState } from 'react'
import {
  Box, Card, CardBody, Heading, Text, HStack, VStack, Button, Tag,
  SimpleGrid, IconButton, useDisclosure, Modal, ModalOverlay, ModalContent,
  ModalHeader, ModalCloseButton, ModalBody, ModalFooter, FormControl,
  FormLabel, Input, Select, Switch, useToast, Icon, Flex, Menu, MenuButton,
  MenuList, MenuItem, Tooltip,
} from '@chakra-ui/react'
import { FiPlus, FiEdit2, FiTrash2, FiMoreVertical, FiHeart, FiCalendar } from 'react-icons/fi'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import PageContainer from '../../components/layout/PageContainer'
import { LoadingState, EmptyState } from '../../components/common/States'
import { anniversaryApi } from '../../api/modules/anniversary.api'

const TYPE_LABEL = {
  ONCE: '一次性',
  ANNIVERSARY: '周年',
  BIRTHDAY_USER_A: 'TA 的生日',
  BIRTHDAY_USER_B: '我的生日',
  VALENTINE: '情人节',
  CUSTOM: '自定义',
}

const TYPE_ICON = {
  ONCE: '🎯',
  ANNIVERSARY: '💝',
  BIRTHDAY_USER_A: '🎂',
  BIRTHDAY_USER_B: '🎂',
  VALENTINE: '🌹',
  CUSTOM: '✨',
}

function CountdownText({ date, isRecurring }) {
  const target = dayjs(date)
  const today = dayjs().startOf('day')
  const diff = target.diff(today, 'day')
  if (diff === 0) return <Text color="brand.500" fontWeight={700}>就是今天！</Text>
  if (diff > 0) {
    return <Text color="brand.500" fontWeight={700}>还有 {diff} 天</Text>
  }
  // 已过 → 如果是 recurring 算下一轮
  if (isRecurring) {
    const next = target.year(today.year())
    const d2 = next.diff(today, 'day')
    return <Text color="gray.500" fontSize="sm">每年循环 · 还有 {d2} 天</Text>
  }
  return <Text color="gray.400" fontSize="sm">已过 {-diff} 天</Text>
}

function AnniversaryCard({ item, onEdit, onDelete }) {
  return (
    <Card>
      <CardBody>
        <HStack align="flex-start" spacing={3}>
          <Box
            w={14} h={14} borderRadius="2xl" display="flex" alignItems="center"
            justifyContent="center" fontSize="3xl"
            bg="brand.50" flexShrink={0}
          >
            {TYPE_ICON[item.type] || '✨'}
          </Box>
          <Box flex={1} minW={0}>
            <HStack>
              <Text fontWeight={700} noOfLines={1}>{item.title}</Text>
              <Tag size="sm" colorScheme="pink" borderRadius="full">
                {TYPE_LABEL[item.type] || '纪念日'}
              </Tag>
            </HStack>
            <Text fontSize="sm" color="gray.500" mt={1}>
              {dayjs(item.date).format('YYYY年M月D日')}
            </Text>
            <Box mt={2}>
              <CountdownText date={item.date} isRecurring={item.is_recurring} />
            </Box>
          </Box>
          <Menu>
            <MenuButton as={IconButton} size="sm" variant="ghost"
              icon={<FiMoreVertical />} aria-label="more" />
            <MenuList>
              <MenuItem icon={<FiEdit2 />} onClick={() => onEdit(item)}>编辑</MenuItem>
              <MenuItem icon={<FiTrash2 />} color="red.500"
                onClick={() => onDelete(item)}>删除</MenuItem>
            </MenuList>
          </Menu>
        </HStack>
      </CardBody>
    </Card>
  )
}

function AnniversariesModal({ isOpen, onClose, initial, onSaved }) {
  const isEdit = !!initial?.id
  const [title, setTitle] = useState(initial?.title || '')
  const [date, setDate] = useState(initial?.date || dayjs().format('YYYY-MM-DD'))
  const [type, setType] = useState(initial?.type || 'ONCE')
  const [isRecurring, setIsRecurring] = useState(initial?.is_recurring || false)
  const [color, setColor] = useState(initial?.color || '#FF6B9D')
  const toast = useToast()
  const queryClient = useQueryClient()

  const saveMut = useMutation({
    mutationFn: () => isEdit
      ? anniversaryApi.update(initial.id, {
          title, date, type, is_recurring: isRecurring, color,
        })
      : anniversaryApi.create({
          title, date, type, is_recurring: isRecurring, color,
        }),
    onSuccess: () => {
      toast({ status: 'success', title: isEdit ? '已更新' : '已创建' })
      queryClient.invalidateQueries({ queryKey: ['anniversaries'] })
      onSaved()
      onClose()
    },
    onError: (err) => {
      toast({ status: 'error', title: '失败', description: err.message })
    },
  })

  return (
    <Modal isOpen={isOpen} onClose={onClose} isCentered>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>{isEdit ? '编辑纪念日' : '新建纪念日'}</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={4}>
            <FormControl isRequired>
              <FormLabel>标题</FormLabel>
              <Input value={title} onChange={(e) => setTitle(e.target.value)}
                placeholder="如：100 天纪念" />
            </FormControl>
            <FormControl isRequired>
              <FormLabel>日期</FormLabel>
              <Input type="date" value={date}
                onChange={(e) => setDate(e.target.value)} />
            </FormControl>
            <FormControl>
              <FormLabel>类型</FormLabel>
              <Select value={type} onChange={(e) => setType(e.target.value)}>
                {Object.entries(TYPE_LABEL).map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </Select>
            </FormControl>
            <FormControl display="flex" alignItems="center">
              <FormLabel mb={0}>每年重复</FormLabel>
              <Switch isChecked={isRecurring}
                onChange={(e) => setIsRecurring(e.target.checked)} colorScheme="pink" />
            </FormControl>
          </VStack>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" mr={2} onClick={onClose}>取消</Button>
          <Button colorScheme="brand"
            isDisabled={!title || !date}
            isLoading={saveMut.isPending}
            onClick={() => saveMut.mutate()}>
            {isEdit ? '保存' : '创建'}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  )
}

export default function Anniversaries() {
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [editing, setEditing] = useState(null)
  const toast = useToast()
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['anniversaries'],
    queryFn: () => anniversaryApi.list(),
  })
  const items = data?.items || data?.data?.items || []

  const delMut = useMutation({
    mutationFn: (id) => anniversaryApi.remove(id),
    onSuccess: () => {
      toast({ status: 'success', title: '已删除' })
      queryClient.invalidateQueries({ queryKey: ['anniversaries'] })
    },
  })

  return (
    <PageContainer
      title="纪念日 💝"
      subtitle="别忘了每一个重要的日子"
      actions={
        <Button colorScheme="brand" leftIcon={<FiPlus />}
          onClick={() => { setEditing(null); onOpen() }}>
          新建
        </Button>
      }
    >
      {isLoading ? (
        <LoadingState />
      ) : items.length === 0 ? (
        <EmptyState
          icon="🎁"
          title="还没有纪念日"
          description="记录你们的每一个重要日子"
          actionLabel="创建第一个"
          onAction={() => onOpen()}
        />
      ) : (
        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
          {items.map((a) => (
            <AnniversaryCard
              key={a.id}
              item={a}
              onEdit={(it) => { setEditing(it); onOpen() }}
              onDelete={(it) => {
                if (window.confirm(`删除「${it.title}」？`)) {
                  delMut.mutate(it.id)
                }
              }}
            />
          ))}
        </SimpleGrid>
      )}

      <AnniversariesModal
        isOpen={isOpen}
        onClose={onClose}
        initial={editing}
        onSaved={() => {}}
      />
    </PageContainer>
  )
}
