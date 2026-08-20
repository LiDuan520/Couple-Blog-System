/**
 * 首页 / 仪表盘
 *
 * 展示：在一起天数大数字、倒计时、最近事件、统计数据、快捷入口
 */
import {
  Box, SimpleGrid, Heading, Text, HStack, VStack, Card, CardBody,
  Stat, StatLabel, StatNumber, StatHelpText, Button, Avatar, AvatarGroup,
  Skeleton, SkeletonText, Tag, Icon, useBreakpointValue,
} from '@chakra-ui/react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { FiCalendar, FiImage, FiBookOpen, FiHeart, FiArrowRight } from 'react-icons/fi'
import dayjs from 'dayjs'
import PageContainer from '../../components/layout/PageContainer'
import { LoadingState, EmptyState } from '../../components/common/States'
import { dashboardApi } from '../../api/modules/timeline.api'
import { useAuthStore } from '../../store/authStore'

function CountdownCard({ item }) {
  const target = dayjs(item.date)
  const today = dayjs().startOf('day')
  const days = target.diff(today, 'day')
  return (
    <Card>
      <CardBody>
        <HStack justify="space-between" align="flex-start" mb={2}>
          <Box>
            <Text fontSize="sm" color="gray.500">{item.title}</Text>
            <Text fontSize="xs" color="gray.400" mt={1}>
              {target.format('YYYY-MM-DD')}
            </Text>
          </Box>
          <Box textAlign="right">
            <Text fontSize="3xl" fontWeight={800}
              bgGradient="linear(to-r, brand.500, purple.500)"
              bgClip="text" lineHeight={1}>
              {days}
            </Text>
            <Text fontSize="xs" color="gray.400">天后</Text>
          </Box>
        </HStack>
      </CardBody>
    </Card>
  )
}

function HeroBanner({ couple, user }) {
  const days = couple?.days_together ?? 0
  return (
    <Box
      borderRadius="3xl" overflow="hidden" position="relative" p={{ base: 6, md: 10 }}
      background="linear-gradient(135deg, #FF6B9D 0%, #B983FF 100%)"
      color="white"
    >
      <Box position="absolute" top={-10} right={-10} fontSize="200px"
        opacity={0.15} lineHeight={1}>💕</Box>
      <Box position="absolute" bottom={-20} left={20} fontSize="120px"
        opacity={0.1} lineHeight={1}>✨</Box>
      <VStack align="flex-start" spacing={3} position="relative">
        <HStack>
          <Text fontSize="sm" opacity={0.9}>💗 在一起</Text>
          {couple?.anniversary_date && (
            <Tag size="sm" bg="whiteAlpha.300" color="white" borderRadius="full">
              恋爱日 {couple.anniversary_date}
            </Tag>
          )}
        </HStack>
        <HStack align="baseline" spacing={2}>
          <Text fontSize={{ base: '6xl', md: '7xl' }} fontWeight={800} lineHeight={1}>
            {days}
          </Text>
          <Text fontSize="2xl" opacity={0.9}>天</Text>
        </HStack>
        {couple?.partner && (
          <HStack pt={2}>
            <AvatarGroup size="sm" max={2}>
              <Avatar name={user?.nickname} src={user?.avatar} />
              <Avatar name={couple.partner.nickname || couple.partner.username} />
            </AvatarGroup>
            <Text fontSize="sm" opacity={0.9}>
              {user?.nickname || user?.username} & {couple.partner.nickname || couple.partner.username}
            </Text>
          </HStack>
        )}
        {!couple && (
          <Button as={Link} to="/couple" mt={2}
            bg="white" color="brand.600" _hover={{ bg: 'whiteAlpha.900' }}
            rightIcon={<FiArrowRight />}>
            绑定 TA
          </Button>
        )}
      </VStack>
    </Box>
  )
}

function RecentEvent({ event }) {
  const iconMap = {
    BLOG: '📝',
    ANNIVERSARY: '💝',
    PHOTO: '📷',
    MILESTONE: '🎉',
  }
  return (
    <HStack
      align="flex-start" p={3} borderRadius="xl"
      _hover={{ bg: 'brand.50' }} transition="all 0.15s"
    >
      <Box fontSize="2xl" lineHeight={1}>{iconMap[event.type] || '✨'}</Box>
      <Box flex={1} minW={0}>
        <Text fontWeight={600} noOfLines={1}>{event.title}</Text>
        <Text fontSize="xs" color="gray.500" noOfLines={1}>
          {event.summary}
        </Text>
      </Box>
      <Text fontSize="xs" color="gray.400" whiteSpace="nowrap">
        {dayjs(event.occurred_at).format('MM-DD')}
      </Text>
    </HStack>
  )
}

function QuickAction({ to, icon, label, color }) {
  return (
    <Button
      as={Link} to={to} h="auto" py={5} px={4}
      variant="ghost" bg="white" borderRadius="2xl"
      _hover={{ bg: color, color: 'white', transform: 'translateY(-2px)' }}
      transition="all 0.2s"
      boxShadow="0 4px 14px rgba(0,0,0,0.06)"
      flexDir="column" gap={1}
    >
      <Icon as={icon} size="24px" />
      <Text fontSize="xs" fontWeight={600}>{label}</Text>
    </Button>
  )
}

export default function Dashboard() {
  const { user, couple } = useAuthStore()
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => dashboardApi.get(),
    enabled: !!couple,
    retry: 0,
  })

  const d = data?.data || data

  return (
    <PageContainer
      title={`你好，${user?.nickname || user?.username || ''} 👋`}
      subtitle={couple ? '这是你们的故事' : '绑定你的 TA，开始记录爱情'}
    >
      <VStack align="stretch" spacing={6}>
        {/* Hero 天数大数字 */}
        <HeroBanner couple={couple} user={user} />

        {/* 已绑定：仪表盘详情 */}
        {couple && isLoading && <LoadingState />}
        {couple && isError && (
          <EmptyState icon="😅" title="加载失败"
            description="请稍后再试"
            actionLabel="重试" onAction={refetch} />
        )}
        {couple && d && (
          <>
            {/* 倒计时 */}
            {d.next_countdown?.length > 0 && (
              <Box>
                <HStack mb={3}>
                  <Icon as={FiHeart} color="brand.500" />
                  <Heading size="md">倒计时</Heading>
                </HStack>
                <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
                  {d.next_countdown.map((c, i) => (
                    <CountdownCard key={i} item={c} />
                  ))}
                </SimpleGrid>
              </Box>
            )}

            {/* 统计 */}
            <SimpleGrid columns={{ base: 2, md: 3 }} spacing={4}>
              <Card><CardBody>
                <Stat>
                  <StatLabel color="gray.500">博客</StatLabel>
                  <StatNumber color="brand.600">{d.stats?.blog_count ?? 0}</StatNumber>
                  <StatHelpText>共记录</StatHelpText>
                </Stat>
              </CardBody></Card>
              <Card><CardBody>
                <Stat>
                  <StatLabel color="gray.500">照片</StatLabel>
                  <StatNumber color="purple.500">{d.stats?.photo_count ?? 0}</StatNumber>
                  <StatHelpText>共珍藏</StatHelpText>
                </Stat>
              </CardBody></Card>
              <Card><CardBody>
                <Stat>
                  <StatLabel color="gray.500">纪念日</StatLabel>
                  <StatNumber color="brand.500">{d.stats?.anniversary_count ?? 0}</StatNumber>
                  <StatHelpText>共庆祝</StatHelpText>
                </Stat>
              </CardBody></Card>
            </SimpleGrid>

            {/* 最近事件 */}
            <Box>
              <HStack mb={3} justify="space-between">
                <HStack>
                  <Icon as={FiCalendar} color="brand.500" />
                  <Heading size="md">最近时光</Heading>
                </HStack>
                <Button as={Link} to="/timeline" size="sm" variant="ghost"
                  rightIcon={<FiArrowRight />}>
                  完整时间轴
                </Button>
              </HStack>
              {d.recent_events?.length > 0 ? (
                <Card><CardBody p={2}>
                  <VStack align="stretch" spacing={1}>
                    {d.recent_events.map((e) => (
                      <RecentEvent key={e.id} event={e} />
                    ))}
                  </VStack>
                </CardBody></Card>
              ) : (
                <EmptyState icon="📭" title="还没有事件"
                  description="写一篇博客、上传一张照片，或者创建一个纪念日吧"
                />
              )}
            </Box>
          </>
        )}

        {/* 快捷入口 */}
        <Box>
          <Heading size="md" mb={3}>快捷入口</Heading>
          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
            <QuickAction to="/blogs/new" icon={FiBookOpen} label="写博客" color="brand.500" />
            <QuickAction to="/anniversaries" icon={FiCalendar} label="纪念日" color="purple.400" />
            <QuickAction to="/albums" icon={FiImage} label="相册" color="brand.400" />
            <QuickAction to="/timeline" icon={FiHeart} label="时间轴" color="purple.500" />
          </SimpleGrid>
        </Box>
      </VStack>
    </PageContainer>
  )
}
