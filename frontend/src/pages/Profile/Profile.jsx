/**
 * 个人资料 - 粉紫少女风
 */
import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box, Card, CardBody, Heading, Text, HStack, VStack, Button, Avatar,
  Input, FormControl, FormLabel, Alert, AlertIcon, useToast,
  Modal, ModalOverlay, ModalContent, ModalHeader, ModalCloseButton,
  ModalBody, ModalFooter, FormErrorMessage, Divider,
} from '@chakra-ui/react'
import { FiArrowLeft, FiCamera, FiSave, FiKey } from 'react-icons/fi'
import PageContainer from '../../components/layout/PageContainer'
import { useAuthStore } from '../../store/authStore'
import { userAPI } from '../../api/modules/user.api'
import { validateInput } from '../../utils/validation'

function Profile() {
  const navigate = useNavigate()
  const toast = useToast()
  const { user, logout, changePassword, updateUser } = useAuthStore()
  const [form, setForm] = useState({
    nickname: user?.nickname || '',
    email: user?.email || '',
  })
  const [saving, setSaving] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const fileRef = useRef(null)

  const [showPwdModal, setShowPwdModal] = useState(false)
  const [pwdForm, setPwdForm] = useState({ old_password: '', new_password: '', confirm: '' })
  const [pwdError, setPwdError] = useState('')
  const [pwdSaving, setPwdSaving] = useState(false)

  useEffect(() => {
    if (!user) navigate('/login')
  }, [user, navigate])

  const handleSave = async () => {
    setErrorMsg('')
    if (form.email && !validateInput.email(form.email)) {
      setErrorMsg('邮箱格式不正确'); return
    }
    setSaving(true)
    try {
      const updated = await userAPI.updateProfile({
        nickname: form.nickname || undefined,
        email: form.email || undefined,
      })
      const data = updated.data || updated
      updateUser(data)
      toast({ status: 'success', title: '保存成功' })
    } catch (e) {
      setErrorMsg(e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleAvatarChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      await userAPI.uploadAvatar(file)
      const me = await userAPI.getProfile()
      updateUser(me.data || me)
      toast({ status: 'success', title: '头像已更新' })
    } catch (e) {
      toast({ status: 'error', title: '上传失败', description: e.message })
    }
  }

  const handleChangePassword = async () => {
    setPwdError('')
    if (!pwdForm.old_password || !pwdForm.new_password) {
      setPwdError('请填写完整'); return
    }
    if (!validateInput.password(pwdForm.new_password)) {
      setPwdError('新密码至少 8 位且包含字母+数字'); return
    }
    if (pwdForm.new_password !== pwdForm.confirm) {
      setPwdError('两次密码不一致'); return
    }
    setPwdSaving(true)
    try {
      const result = await changePassword({
        old_password: pwdForm.old_password,
        new_password: pwdForm.new_password,
      })
      if (result.success) {
        setShowPwdModal(false)
        toast({ status: 'success', title: '密码已更新' })
        await logout()
        navigate('/login')
      } else {
        setPwdError(result.error || '修改失败')
      }
    } catch (e) {
      setPwdError(e.message)
    } finally {
      setPwdSaving(false)
    }
  }

  const avatarSrc = userAPI.avatarSrc(user?.avatar)

  return (
    <PageContainer
      title="个人资料"
      actions={
        <Button variant="ghost" leftIcon={<FiArrowLeft />} onClick={() => navigate('/')}>
          返回
        </Button>
      }
    >
      <VStack spacing={6} align="stretch" maxW="2xl" mx="auto">
        {/* 头像卡片 */}
        <Card>
          <CardBody>
            <HStack spacing={6}>
              <Avatar
                size="2xl" name={user?.nickname || user?.username}
                src={avatarSrc}
                bg="brand.300" color="white"
              />
              <Box>
                <Heading size="md">{user?.nickname || user?.username}</Heading>
                <Text color="gray.500" mb={3}>@{user?.username}</Text>
                <input ref={fileRef} type="file" accept="image/*" hidden
                  onChange={handleAvatarChange} />
                <Button size="sm" leftIcon={<FiCamera />} colorScheme="brand"
                  variant="outline" onClick={() => fileRef.current?.click()}>
                  更换头像
                </Button>
                <Text fontSize="xs" color="gray.400" mt={2}>
                  支持 jpg/png/gif/webp，最大 2MB
                </Text>
              </Box>
            </HStack>
          </CardBody>
        </Card>

        {/* 资料表单 */}
        <Card>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <FormControl>
                <FormLabel>用户名（不可改）</FormLabel>
                <Input value={user?.username || ''} isDisabled bg="gray.50" />
              </FormControl>
              <FormControl>
                <FormLabel>昵称</FormLabel>
                <Input value={form.nickname}
                  onChange={(e) => setForm({ ...form, nickname: e.target.value })}
                  maxLength={100} />
              </FormControl>
              <FormControl>
                <FormLabel>邮箱</FormLabel>
                <Input type="email" value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })} />
              </FormControl>

              {errorMsg && (
                <Alert status="error" borderRadius="md">
                  <AlertIcon />{errorMsg}
                </Alert>
              )}

              <HStack>
                <Button colorScheme="brand" flex={1}
                  leftIcon={<FiSave />} isLoading={saving} onClick={handleSave}>
                  保存
                </Button>
                <Button flex={1} leftIcon={<FiKey />} variant="outline"
                  colorScheme="brand" onClick={() => setShowPwdModal(true)}>
                  修改密码
                </Button>
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        {/* 情侣信息（如有） */}
        {user?.couple && (
          <Card>
            <CardBody>
              <Heading size="sm" mb={3} color="brand.600">💕 情侣信息</Heading>
              <Divider mb={3} />
              <HStack>
                <Avatar size="md" name={user.couple.partner?.nickname} />
                <Box>
                  <Text fontWeight={700}>
                    {user.couple.partner?.nickname || user.couple.partner?.username}
                  </Text>
                  <Text fontSize="sm" color="gray.500">
                    @{user.couple.partner?.username}
                  </Text>
                </Box>
                <Box ml="auto" textAlign="right">
                  <Text fontSize="sm" color="gray.500">恋爱日</Text>
                  <Text fontWeight={700}>{user.couple.anniversary_date}</Text>
                </Box>
              </HStack>
            </CardBody>
          </Card>
        )}
      </VStack>

      {/* 修改密码弹窗 */}
      <Modal isOpen={showPwdModal} onClose={() => setShowPwdModal(false)} isCentered>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>修改密码</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>旧密码</FormLabel>
                <Input type="password" value={pwdForm.old_password}
                  onChange={(e) => setPwdForm({ ...pwdForm, old_password: e.target.value })} />
              </FormControl>
              <FormControl isRequired isInvalid={pwdError && pwdError.includes('新密码')}>
                <FormLabel>新密码</FormLabel>
                <Input type="password" value={pwdForm.new_password}
                  onChange={(e) => setPwdForm({ ...pwdForm, new_password: e.target.value })} />
                <FormErrorMessage>{pwdError}</FormErrorMessage>
              </FormControl>
              <FormControl isRequired isInvalid={pwdError && pwdError.includes('一致')}>
                <FormLabel>确认新密码</FormLabel>
                <Input type="password" value={pwdForm.confirm}
                  onChange={(e) => setPwdForm({ ...pwdForm, confirm: e.target.value })} />
                <FormErrorMessage>{pwdError}</FormErrorMessage>
              </FormControl>
              {pwdError && !pwdError.includes('新密码') && !pwdError.includes('一致') && (
                <Alert status="error" borderRadius="md"><AlertIcon />{pwdError}</Alert>
              )}
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={2} onClick={() => setShowPwdModal(false)}>
              取消
            </Button>
            <Button colorScheme="brand" isLoading={pwdSaving}
              onClick={handleChangePassword}>确认</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </PageContainer>
  )
}

export default Profile
