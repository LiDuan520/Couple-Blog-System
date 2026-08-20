/**
 * 情侣中心
 *
 * 三种状态：
 * 1. 已绑定 → 显示伴侣信息 + 恋爱日 + 操作（解绑）
 * 2. 有待接受邀请 → 显示自己的邀请码 + 复制 + 撤销
 * 3. 未绑定且无邀请 → 显示「生成邀请码」按钮 + 接受别人邀请输入框
 */
import { useState } from 'react'
import {
  Box, Card, CardBody, Heading, Text, HStack, VStack, Button, Avatar,
  Tag, Input, FormControl, FormLabel, useToast, SimpleGrid, useClipboard,
  Divider, IconButton, useDisclosure, Modal, ModalOverlay, ModalContent,
  ModalHeader, ModalBody, ModalFooter, ModalCloseButton, Alert, AlertIcon,
} from '@chakra-ui/react'
import { FiCopy, FiTrash2, FiHeart, FiUserPlus, FiLink2 } from 'react-icons/fi'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import PageContainer from '../../components/layout/PageContainer'
import { LoadingState } from '../../components/common/States'
import { coupleApi } from '../../api/modules/couple.api'
import { useAuthStore } from '../../store/authStore'

function BoundView({ couple, user, onUnbind }) {
  return (
    <VStack spacing={6}>
      <Box
        w="full" borderRadius="3xl" p={{ base: 6, md: 10 }}
        background="linear-gradient(135deg, #FF6B9D 0%, #B983FF 100%)"
        color="white" position="relative" overflow="hidden"
      >
        <Box position="absolute" top={-20} right={-20}
          fontSize="240px" opacity={0.12} lineHeight={1}>💞</Box>
        <HStack spacing={4} align="center" position="relative">
          <Avatar size="xl" name={user?.nickname} src={user?.avatar}
            border="4px solid white" />
          <Box fontSize="3xl">💗</Box>
          <Avatar size="xl" name={couple.partner?.nickname}
            src={couple.partner?.avatar}
            border="4px solid white" />
        </HStack>
        <VStack mt={6} spacing={2} position="relative" align="flex-start">
          <Text fontSize="sm" opacity={0.9}>💕 恋爱日</Text>
          <Text fontSize="3xl" fontWeight={800}>
            {dayjs(couple.anniversary_date).format('YYYY年M月D日')}
          </Text>
          <HStack pt={1}>
            <Tag bg="whiteAlpha.300" color="white" borderRadius="full">
              在一起 {couple.days_together} 天
            </Tag>
          </HStack>
        </VStack>
      </Box>

      <Card w="full">
        <CardBody>
          <Heading size="sm" mb={4} color="gray.600">伴侣信息</Heading>
          <HStack>
            <Avatar size="md" name={couple.partner?.nickname} />
            <Box flex={1}>
              <Text fontWeight={700}>
                {couple.partner?.nickname || couple.partner?.username}
              </Text>
              <Text fontSize="sm" color="gray.500">
                @{couple.partner?.username}
              </Text>
            </Box>
            <Button leftIcon={<FiTrash2 />} variant="ghost" colorScheme="red"
              size="sm" onClick={onUnbind}>
              解绑
            </Button>
          </HStack>
        </CardBody>
      </Card>
    </VStack>
  )
}

function InviteView({ invite, onRevoke }) {
  const { onCopy, hasCopied, setValue } = useClipboard(invite?.code || '')
  return (
    <VStack spacing={6}>
      <Box
        w="full" borderRadius="3xl" p={{ base: 6, md: 10 }}
        background="linear-gradient(135deg, #B983FF 0%, #94D0FF 100%)"
        color="white" textAlign="center"
      >
        <Text fontSize="6xl" mb={2}>💌</Text>
        <Text fontSize="lg" fontWeight={700}>你的专属邀请码</Text>
        <Text fontSize="sm" opacity={0.9} mt={1}>
          把这串甜蜜告诉 TA，等 TA 接受
        </Text>
        <HStack
          mt={6} bg="whiteAlpha.300" borderRadius="2xl" p={4}
          justify="center" spacing={3}
        >
          <Text fontSize="4xl" fontWeight={800} letterSpacing="0.3em"
            fontFamily="mono">
            {invite?.code}
          </Text>
          <IconButton
            icon={<FiCopy />} aria-label="copy" variant="ghost"
            color="white" _hover={{ bg: 'whiteAlpha.300' }}
            onClick={() => { setValue(invite.code); onCopy() }}
          />
        </HStack>
        <Text fontSize="xs" opacity={0.8} mt={3}>
          {hasCopied ? '✓ 已复制到剪贴板' :
            `过期时间：${dayjs(invite?.expires_at).format('MM-DD HH:mm')}`}
        </Text>
      </Box>
      <Button variant="outline" colorScheme="red" leftIcon={<FiTrash2 />}
        onClick={onRevoke}>
        撤销邀请
      </Button>
    </VStack>
  )
}

function UnboundView({ onCreated }) {
  const [code, setCode] = useState('')
  const [date, setDate] = useState('')
  const toast = useToast()
  const queryClient = useQueryClient()

  const createMut = useMutation({
    mutationFn: () => coupleApi.createInvite(),
    onSuccess: (res) => {
      const inv = res.data || res
      onCreated(inv)
      queryClient.invalidateQueries({ queryKey: ['my-invite'] })
    },
    onError: (err) => {
      toast({ status: 'error', title: '生成失败', description: err.message })
    },
  })

  const acceptMut = useMutation({
    mutationFn: ({ code, date }) =>
      coupleApi.acceptInvite(code, date),
    onSuccess: () => {
      toast({ status: 'success', title: '绑定成功 💕' })
      queryClient.invalidateQueries({ queryKey: ['me'] })
      window.location.reload()
    },
    onError: (err) => {
      toast({ status: 'error', title: '接受失败', description: err.message })
    },
  })

  return (
    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
      <Card>
        <CardBody>
          <HStack mb={3} color="brand.500">
            <FiUserPlus />
            <Heading size="md">生成邀请</Heading>
          </HStack>
          <Text color="gray.500" fontSize="sm" mb={4}>
            给 TA 一串专属邀请码，TA 输入后就能绑定你们
          </Text>
          <Button colorScheme="brand" w="full"
            isLoading={createMut.isPending}
            onClick={() => createMut.mutate()}>
            生成邀请码
          </Button>
        </CardBody>
      </Card>

      <Card>
        <CardBody>
          <HStack mb={3} color="purple.500">
            <FiLink2 />
            <Heading size="md">接受邀请</Heading>
          </HStack>
          <Text color="gray.500" fontSize="sm" mb={4}>
            收到 TA 的邀请码？输入并设置你们的恋爱日
          </Text>
          <VStack spacing={3}>
            <FormControl>
              <FormLabel fontSize="sm">邀请码</FormLabel>
              <Input value={code} onChange={(e) => setCode(e.target.value.toUpperCase())}
                placeholder="8 位邀请码" maxLength={8} />
            </FormControl>
            <FormControl>
              <FormLabel fontSize="sm">恋爱日</FormLabel>
              <Input type="date" value={date}
                onChange={(e) => setDate(e.target.value)} />
            </FormControl>
            <Button colorScheme="purple" w="full"
              isLoading={acceptMut.isPending}
              isDisabled={!code || !date}
              onClick={() => acceptMut.mutate({ code, date })}>
              接受并绑定
            </Button>
          </VStack>
        </CardBody>
      </Card>
    </SimpleGrid>
  )
}

export default function Couple() {
  const { user, setCouple, refreshCouple } = useAuthStore()
  const toast = useToast()
  const queryClient = useQueryClient()
  const { isOpen, onOpen, onClose } = useDisclosure()

  // 当前 couple
  const { data: meData, isLoading: meLoading } = useQuery({
    queryKey: ['couple-me'],
    queryFn: () => coupleApi.getMe(),
    retry: 0,
  })
  const coupleInfo = meData?.data || meData

  // 我的邀请码
  const { data: invData, isLoading: invLoading } = useQuery({
    queryKey: ['my-invite'],
    queryFn: () => coupleApi.getMyInvite(),
    retry: 0,
  })
  const myInvite = invData?.data || invData

  const revokeMut = useMutation({
    mutationFn: () => coupleApi.revokeInvite(),
    onSuccess: () => {
      toast({ status: 'success', title: '已撤销' })
      queryClient.invalidateQueries({ queryKey: ['my-invite'] })
    },
  })

  const unbindMut = useMutation({
    mutationFn: () => coupleApi.delete(),
    onSuccess: () => {
      toast({ status: 'success', title: '已解绑' })
      setCouple(null)
      onClose()
      queryClient.invalidateQueries({ queryKey: ['couple-me'] })
    },
  })

  if (meLoading || invLoading) return <LoadingState />

  const hasCouple = coupleInfo?.couple?.id
  const hasInvite = myInvite?.code

  return (
    <PageContainer title="情侣中心" subtitle="记录你们两个人的故事">
      {hasCouple ? (
        <BoundView
          couple={coupleInfo.couple}
          user={user}
          onUnbind={onOpen}
        />
      ) : hasInvite ? (
        <InviteView
          invite={myInvite}
          onRevoke={() => revokeMut.mutate()}
        />
      ) : (
        <UnboundView
          onCreated={(inv) => {
            queryClient.setQueryData(['my-invite'], { data: inv })
            queryClient.invalidateQueries({ queryKey: ['my-invite'] })
          }}
        />
      )}

      {/* 解绑确认 */}
      <Modal isOpen={isOpen} onClose={onClose} isCentered>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>解绑？</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Alert status="warning" borderRadius="md">
              <AlertIcon />
              <Text fontSize="sm">解绑后你们的纪念日、相册将不再共享，谨慎操作</Text>
            </Alert>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={2} onClick={onClose}>再想想</Button>
            <Button colorScheme="red"
              isLoading={unbindMut.isPending}
              onClick={() => unbindMut.mutate()}>
              确认解绑
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </PageContainer>
  )
}
