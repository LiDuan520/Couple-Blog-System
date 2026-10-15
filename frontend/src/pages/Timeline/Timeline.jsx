/**
 * 时间轴
 *
 * - 聚合 4 类事件（blog / anniversary / photo / milestone）
 * - 按时间倒序
 * - 过滤：事件类型 / 作者 / 日期范围
 * - 里程碑卡片（特殊样式）
 */
import { useState } from 'react'
import {
  Box, Card, CardBody, Heading, Text, HStack, VStack, Tag, Button,
  Select, Avatar, Icon, Divider, Wrap, WrapItem, useBreakpointValue,
  Container,
} from '@chakra-ui/react'
import { FiBookOpen, FiCalendar, FiImage, FiAward, FiFilter } from 'react-icons/fi'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'
import PageContainer from '../../components/layout/PageContainer'
import { LoadingState, EmptyState } from '../../components/common/States'
import { timelineApi } from '../../api/modules/timeline.api'

const TYPE_META = {
  BLOG: { label: '博客', icon: FiBookOpen, color: 'brand' },
  ANNIVERSARY: { label: '纪念日', icon: FiCalendar, color: 'purple' },
  PHOTO: { label: '照片', icon: FiImage, color: 'pink' },
  MILESTONE: { label: '里程碑', icon: FiAward, color: 'yellow' },
}

function MilestoneCard({ item }) {
  return (
    <Card overflow="hidden" position="relative">
      <Box
        h="3" bgGradient="linear(to-r, yellow.300, orange.400)"
      />
      <CardBody>
        <HStack mb={2}>
          <Icon as={FiAward} color="orange.400" />
          <Text fontWeight={800} fontSize="lg">
            {item.title}
          </Text>
        </HStack>
        <Text color="gray.500" fontSize="sm" mb={3}>
          🎉 {item.description}
        </Text>
        <Tag size="sm" colorScheme="yellow" borderRadius="full">
          {dayjs(item.date).format('YYYY年M月D日')}
        </Tag>
      </CardBody>
    </Card>
  )
}

function EventItem({ event }) {
  const meta = TYPE_META[event.type] || TYPE_META.BLOG
  return (
    <HStack align="flex-start" spacing={4}>
      <VStack spacing={1} pt={1}>
        <Box
          w={10} h={10} borderRadius="full" display="flex"
          alignItems="center" justifyContent="center"
          bg={`${meta.color}.100`} color={`${meta.color}.500`}
        >
          <Icon as={meta.icon} />
        </Box>
      </VStack>
      <Card flex={1}>
        <CardBody>
          <HStack mb={2}>
            <Tag size="sm" colorScheme={meta.color} borderRadius="full">
              {meta.label}
            </Tag>
            <Text fontSize="xs" color="gray.400">
              {dayjs(event.occurred_at).format('YYYY-MM-DD HH:mm')}
            </Text>
            {event.author && (
              <HStack spacing={1} ml="auto">
                <Avatar size="xs" name={event.author.nickname} />
                <Text fontSize="xs" color="gray.500">
                  {event.author.nickname || event.author.username}
                </Text>
              </HStack>
            )}
          </HStack>
          <Text fontWeight={700}>{event.title}</Text>
          {event.summary && (
            <Text fontSize="sm" color="gray.600" noOfLines={2} mt={1}>
              {event.summary}
            </Text>
          )}
          {event.url && (
            <Box mt={2}>
              <img src={event.url} alt=""
                style={{ maxWidth: '100%', maxHeight: 200, borderRadius: 12 }} />
            </Box>
          )}
        </CardBody>
      </Card>
    </HStack>
  )
}

function MilestoneSummaryCard({ items }) {
  if (!items || items.length === 0) return null
  return (
    <Card mb={6} bg="white">
      <CardBody>
        <HStack mb={3}>
          <Icon as={FiAward} color="orange.400" />
          <Heading size="sm">即将到来的里程碑</Heading>
        </HStack>
        <Wrap spacing={2}>
          {items.map((m, i) => (
            <WrapItem key={i}>
              <Tag size="lg" colorScheme="orange" borderRadius="full" py={2} px={4}>
                <VStack spacing={0} align="flex-start">
                  <Text fontWeight={700}>{m.title}</Text>
                  <Text fontSize="xs" color="orange.700">
                    {dayjs(m.date).format('YYYY-MM-DD')}
                  </Text>
                </VStack>
              </Tag>
            </WrapItem>
          ))}
        </Wrap>
      </CardBody>
    </Card>
  )
}

export default function Timeline() {
  const [type, setType] = useState('')
  const [author, setAuthor] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 20

  const params = {
    page, page_size: pageSize,
    type: type || undefined,
    author_user_id: author || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  }
  const { data, isLoading } = useQuery({
    queryKey: ['timeline', params],
    queryFn: () => timelineApi.list(params),
  })
  const t = data?.data || data
  const events = t?.items || []
  const milestones = t?.milestones || []
  const totalPages = t?.total_pages || 1

  return (
    <PageContainer title="时间轴 ⏳" subtitle="属于你们的时光印记">
      <MilestoneSummaryCard items={milestones} />

      {/* 过滤栏 */}
      <Card mb={6}>
        <CardBody py={3}>
          <Wrap spacing={3} align="center">
            <WrapItem>
              <HStack>
                <Icon as={FiFilter} color="brand.500" />
                <Text fontSize="sm" color="gray.600">筛选</Text>
              </HStack>
            </WrapItem>
            <WrapItem>
              <Select size="sm" w="auto" value={type}
                onChange={(e) => { setType(e.target.value); setPage(1) }}>
                <option value="">全部类型</option>
                {Object.entries(TYPE_META).map(([v, m]) => (
                  <option key={v} value={v}>{m.label}</option>
                ))}
              </Select>
            </WrapItem>
            <WrapItem>
              <Select size="sm" w="auto" value={author}
                onChange={(e) => { setAuthor(e.target.value); setPage(1) }}>
                <option value="">全部作者</option>
                <option value="me">我</option>
                <option value="partner">TA</option>
              </Select>
            </WrapItem>
            <WrapItem>
              <HStack>
                <Text fontSize="xs" color="gray.500">从</Text>
                <Input type="date" size="sm" w="auto" value={dateFrom}
                  onChange={(e) => { setDateFrom(e.target.value); setPage(1) }} />
              </HStack>
            </WrapItem>
            <WrapItem>
              <HStack>
                <Text fontSize="xs" color="gray.500">至</Text>
                <Input type="date" size="sm" w="auto" value={dateTo}
                  onChange={(e) => { setDateTo(e.target.value); setPage(1) }} />
              </HStack>
            </WrapItem>
            {(type || author || dateFrom || dateTo) && (
              <WrapItem>
                <Button size="xs" variant="ghost"
                  onClick={() => {
                    setType(''); setAuthor(''); setDateFrom(''); setDateTo(''); setPage(1)
                  }}>
                  清除
                </Button>
              </WrapItem>
            )}
          </Wrap>
        </CardBody>
      </Card>

      {isLoading ? (
        <LoadingState />
      ) : events.length === 0 ? (
        <EmptyState
          icon="⏳"
          title="还没有事件"
          description="开始记录你们的甜蜜时光吧"
        />
      ) : (
        <>
          <VStack align="stretch" spacing={4}>
            {events.map((e, i) => (
              <EventItem key={`${e.type}-${e.id || i}`} event={e} />
            ))}
          </VStack>

          {totalPages > 1 && (
            <HStack justify="center" mt={6} spacing={2}>
              <Button size="sm" isDisabled={page <= 1}
                onClick={() => setPage(page - 1)}>上一页</Button>
              <Text fontSize="sm" color="gray.500">
                {page} / {totalPages}
              </Text>
              <Button size="sm" isDisabled={page >= totalPages}
                onClick={() => setPage(page + 1)}>下一页</Button>
            </HStack>
          )}
        </>
      )}
    </PageContainer>
  )
}
