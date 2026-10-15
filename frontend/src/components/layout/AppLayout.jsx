/**
 * 应用主布局
 *
 * - 桌面端：固定侧边栏 + 顶部 Header + 主内容区
 * - 移动端：顶部 Header + Drawer 侧边栏
 */
import {
  Box, Flex, HStack, VStack, Text, Avatar, Menu, MenuButton,
  MenuList, MenuItem, MenuDivider, IconButton, useDisclosure,
  Drawer, DrawerOverlay, DrawerContent, DrawerCloseButton, DrawerBody,
  useBreakpointValue, Tag, Tooltip,
} from '@chakra-ui/react'
import { Link, useLocation, useNavigate, Outlet } from 'react-router-dom'
import { FiMenu, FiLogOut, FiUser, FiHome, FiBookOpen,
  FiCalendar, FiImage, FiClock } from 'react-icons/fi'
import { useAuthStore } from '../../store/authStore'

const NAV = [
  { to: '/', label: '首页', icon: FiHome },
  { to: '/couple', label: '情侣', icon: FiUser },
  { to: '/blogs', label: '博客', icon: FiBookOpen },
  { to: '/anniversaries', label: '纪念日', icon: FiCalendar },
  { to: '/albums', label: '相册', icon: FiImage },
  { to: '/timeline', label: '时间轴', icon: FiClock },
]

function NavItem({ to, label, icon: Icon, active, onClick }) {
  return (
    <Link to={to} onClick={onClick}>
      <HStack
        px={4} py={3} borderRadius="xl"
        bg={active ? 'rgba(255, 107, 157, 0.15)' : 'transparent'}
        color={active ? 'brand.600' : 'gray.600'}
        fontWeight={active ? 700 : 500}
        _hover={{ bg: 'rgba(255, 107, 157, 0.1)', color: 'brand.500' }}
        transition="all 0.15s"
        spacing={3}
        cursor="pointer"
      >
        <Box as={Icon} size="18px" />
        <Text>{label}</Text>
      </HStack>
    </Link>
  )
}

function SidebarContent({ onClose }) {
  const location = useLocation()
  return (
    <VStack align="stretch" spacing={1} p={4}>
      <Flex align="center" px={2} py={4} mb={2}>
        <Text fontSize="2xl" mr={2}>💕</Text>
        <Text fontWeight={800} fontSize="xl"
          bgGradient="linear(to-r, brand.500, purple.400)"
          bgClip="text">恋爱日记</Text>
      </Flex>
      {NAV.map((item) => (
        <NavItem
          key={item.to}
          {...item}
          active={location.pathname === item.to ||
            (item.to !== '/' && location.pathname.startsWith(item.to))}
          onClick={onClose}
        />
      ))}
    </VStack>
  )
}

function TopBar({ onOpenMenu }) {
  const navigate = useNavigate()
  const { user, logout, couple } = useAuthStore()

  return (
    <Flex
      as="header" h="64px" px={4} align="center" justify="space-between"
      bg="rgba(255, 255, 255, 0.7)" backdropFilter="blur(10px)"
      borderBottom="1px solid" borderColor="brand.100"
      position="sticky" top={0} zIndex={20}
    >
      <HStack>
        <IconButton
          display={{ base: 'inline-flex', md: 'none' }}
          icon={<FiMenu />} variant="ghost" onClick={onOpenMenu}
          aria-label="menu" color="brand.500"
        />
        <Text display={{ base: 'none', md: 'block' }}
          fontWeight={700} color="brand.600">
          {couple ? `💗 与 TA 在一起 ${couple.days_together ?? 0} 天` : '💗 欢迎'}
        </Text>
      </HStack>

      <HStack spacing={3}>
        {couple && (
          <Tooltip label="恋爱日" placement="bottom">
            <Tag size="sm" colorScheme="pink" borderRadius="full">
              {couple.anniversary_date}
            </Tag>
          </Tooltip>
        )}
        <Menu>
          <MenuButton>
            <Avatar
              size="sm" name={user?.nickname || user?.username}
              src={user?.avatar}
              bg="brand.300" color="white"
            />
          </MenuButton>
          <MenuList borderRadius="xl" border="none"
            boxShadow="0 8px 32px rgba(0,0,0,0.12)">
            <Box px={3} py={2}>
              <Text fontWeight={700}>{user?.nickname || user?.username}</Text>
              <Text fontSize="xs" color="gray.500">@{user?.username}</Text>
            </Box>
            <MenuDivider />
            <MenuItem icon={<FiUser />} onClick={() => navigate('/profile')}>
              个人资料
            </MenuItem>
            <MenuDivider />
            <MenuItem icon={<FiLogOut />} color="red.500"
              onClick={async () => { await logout(); navigate('/login') }}>
              登出
            </MenuItem>
          </MenuList>
        </Menu>
      </HStack>
    </Flex>
  )
}

export default function AppLayout() {
  const { isOpen, onOpen, onClose } = useDisclosure()
  const isMobile = useBreakpointValue({ base: true, md: false })

  return (
    <Flex minH="100vh">
      {/* 桌面侧边栏 */}
      {!isMobile && (
        <Box
          as="aside" w="240px" position="fixed" h="100vh"
          bg="rgba(255, 255, 255, 0.6)" backdropFilter="blur(16px)"
          borderRight="1px solid" borderColor="brand.100"
          zIndex={10}
        >
          <SidebarContent />
        </Box>
      )}

      {/* 移动 Drawer */}
      {isMobile && (
        <Drawer isOpen={isOpen} placement="left" onClose={onClose}>
          <DrawerOverlay />
          <DrawerContent bg="rgba(255, 255, 255, 0.95)" maxW="260px">
            <DrawerCloseButton mt={2} />
            <DrawerBody p={0}>
              <SidebarContent onClose={onClose} />
            </DrawerBody>
          </DrawerContent>
        </Drawer>
      )}

      {/* 主区域 */}
      <Flex direction="column" flex={1} ml={{ base: 0, md: '240px' }}>
        <TopBar onOpenMenu={onOpen} />
        <Box as="main" flex={1} p={{ base: 4, md: 8 }}>
          <Outlet />
        </Box>
      </Flex>
    </Flex>
  )
}
