/**
 * 注册页 - 粉紫少女风
 */
import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  Box, Container, Card, CardBody, Heading, Text, VStack,
  Input, InputGroup, InputRightElement, Button, FormControl, FormLabel,
  FormErrorMessage, IconButton, Progress, HStack, useToast,
} from '@chakra-ui/react'
import { FiEye, FiEyeOff } from 'react-icons/fi'
import { useAuthStore } from '../../store/authStore'
import { validateInput } from '../../utils/validation'

function Register() {
  const navigate = useNavigate()
  const toast = useToast()
  const { register, isAuthenticated, isLoading, error, clearError } = useAuthStore()
  const [formData, setFormData] = useState({
    username: '', email: '', password: '',
    confirmPassword: '', nickname: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [touched, setTouched] = useState({})

  useEffect(() => {
    if (isAuthenticated) navigate('/')
  }, [isAuthenticated, navigate])

  useEffect(() => () => clearError(), [clearError])

  const errors = {
    username: formData.username && !validateInput.username(formData.username)
      ? '3-50 字符，仅字母数字下划线' : '',
    email: formData.email && !validateInput.email(formData.email)
      ? '邮箱格式不正确' : '',
    password: formData.password && !validateInput.password(formData.password)
      ? '至少 8 位且包含字母+数字' : '',
    confirmPassword: formData.confirmPassword && formData.confirmPassword !== formData.password
      ? '两次密码不一致' : '',
  }
  const hasError = Object.values(errors).some(Boolean)
  const strength = validateInput.passwordStrength(formData.password)
  const strengthColor = validateInput.passwordStrengthColor(strength)
  const strengthLabel = validateInput.passwordStrengthLabel(strength)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setTouched({ username: true, email: true, password: true, confirmPassword: true })
    if (hasError) return
    const { confirmPassword, ...payload } = formData
    const result = await register(payload)
    if (result.success) {
      toast({ status: 'success', title: '注册成功 💕' })
      navigate('/')
    }
  }

  return (
    <Box minH="100vh" display="flex" alignItems="center" justifyContent="center" p={4}>
      <Container maxW="md" py={8}>
        <VStack spacing={6}>
          <VStack spacing={2}>
            <Text fontSize="5xl">🌸</Text>
            <Heading size="xl"
              bgGradient="linear(to-r, brand.500, purple.500)" bgClip="text">
              加入我们
            </Heading>
            <Text color="gray.500">开始你的爱情日记</Text>
          </VStack>

          <Card w="full">
            <CardBody>
              <form onSubmit={handleSubmit} noValidate>
                <VStack spacing={4}>
                  <FormControl isInvalid={touched.username && !!errors.username}>
                    <FormLabel>用户名</FormLabel>
                    <Input
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      onBlur={() => setTouched({ ...touched, username: true })}
                      autoComplete="username"
                    />
                    <FormErrorMessage>{errors.username}</FormErrorMessage>
                  </FormControl>

                  <FormControl isInvalid={touched.email && !!errors.email}>
                    <FormLabel>邮箱</FormLabel>
                    <Input
                      type="email" value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      onBlur={() => setTouched({ ...touched, email: true })}
                      autoComplete="email"
                    />
                    <FormErrorMessage>{errors.email}</FormErrorMessage>
                  </FormControl>

                  <FormControl isInvalid={touched.password && !!errors.password}>
                    <FormLabel>密码</FormLabel>
                    <InputGroup>
                      <Input
                        type={showPassword ? 'text' : 'password'}
                        value={formData.password}
                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                        onBlur={() => setTouched({ ...touched, password: true })}
                        autoComplete="new-password"
                      />
                      <InputRightElement>
                        <IconButton
                          variant="ghost" size="sm" aria-label="toggle"
                          icon={showPassword ? <FiEyeOff /> : <FiEye />}
                          onClick={() => setShowPassword(!showPassword)}
                        />
                      </InputRightElement>
                    </InputGroup>
                    {formData.password && (
                      <HStack mt={2} spacing={2}>
                        <Progress
                          value={(strength + 1) * 25}
                          size="xs" colorScheme={strengthColor.split('.')[0]}
                          flex={1} borderRadius="full"
                        />
                        <Text fontSize="xs" color={`${strengthColor}.500`}>
                          {strengthLabel}
                        </Text>
                      </HStack>
                    )}
                    <FormErrorMessage>{errors.password}</FormErrorMessage>
                  </FormControl>

                  <FormControl isInvalid={touched.confirmPassword && !!errors.confirmPassword}>
                    <FormLabel>确认密码</FormLabel>
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      value={formData.confirmPassword}
                      onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                      onBlur={() => setTouched({ ...touched, confirmPassword: true })}
                      autoComplete="new-password"
                    />
                    <FormErrorMessage>{errors.confirmPassword}</FormErrorMessage>
                  </FormControl>

                  <FormControl>
                    <FormLabel>昵称（可选）</FormLabel>
                    <Input
                      value={formData.nickname}
                      onChange={(e) => setFormData({ ...formData, nickname: e.target.value })}
                      maxLength={100} placeholder="默认使用用户名"
                    />
                  </FormControl>

                  {error && (
                    <Box w="full" p={3} borderRadius="md" bg="red.50" color="red.600"
                      fontSize="sm" textAlign="center">
                      {error}
                    </Box>
                  )}

                  <Button type="submit" colorScheme="brand" w="full" size="lg"
                    isLoading={isLoading} isDisabled={hasError}>
                    注册
                  </Button>
                </VStack>
              </form>
            </CardBody>
          </Card>

          <Text color="gray.500">
            已有账号？
            <Link to="/login">
              <Text as="span" color="brand.500" fontWeight={600} ml={1}>
                立即登录
              </Text>
            </Link>
          </Text>
        </VStack>
      </Container>
    </Box>
  )
}

export default Register
