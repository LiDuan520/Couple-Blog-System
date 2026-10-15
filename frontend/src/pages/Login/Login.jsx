/**
 * 登录页 - 粉紫少女风
 */
import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  Box, Container, Card, CardBody, Heading, Text, HStack, VStack,
  Input, InputGroup, InputRightElement, Button, FormControl, FormLabel,
  FormErrorMessage, Checkbox, IconButton, Icon, useToast,
} from '@chakra-ui/react'
import { FiEye, FiEyeOff, FiHeart } from 'react-icons/fi'
import { useAuthStore } from '../../store/authStore'
import { validateInput } from '../../utils/validation'

function Login() {
  const navigate = useNavigate()
  const toast = useToast()
  const { login, isAuthenticated, isLoading, error, clearError } = useAuthStore()
  const [formData, setFormData] = useState({
    username: '', password: '', remember_me: false,
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
    password: formData.password && formData.password.length < 8
      ? '至少 8 位' : '',
  }
  const hasError = Object.values(errors).some(Boolean)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setTouched({ username: true, password: true })
    if (hasError) return
    const result = await login(formData)
    if (result.success) {
      toast({ status: 'success', title: '欢迎回来 💕' })
      navigate('/')
    }
  }

  return (
    <Box minH="100vh" display="flex" alignItems="center" justifyContent="center" p={4}>
      <Container maxW="md">
        <VStack spacing={6}>
          <VStack spacing={2}>
            <Text fontSize="5xl">💕</Text>
            <Heading size="xl"
              bgGradient="linear(to-r, brand.500, purple.500)" bgClip="text">
              恋爱日记
            </Heading>
            <Text color="gray.500">记录你们的故事</Text>
          </VStack>

          <Card w="full">
            <CardBody>
              <form onSubmit={handleSubmit} noValidate>
                <VStack spacing={4}>
                  <FormControl isInvalid={touched.username && !!errors.username}>
                    <FormLabel>用户名 / 邮箱</FormLabel>
                    <Input
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      onBlur={() => setTouched({ ...touched, username: true })}
                      placeholder="alice"
                    />
                    <FormErrorMessage>{errors.username}</FormErrorMessage>
                  </FormControl>

                  <FormControl isInvalid={touched.password && !!errors.password}>
                    <FormLabel>密码</FormLabel>
                    <InputGroup>
                      <Input
                        type={showPassword ? 'text' : 'password'}
                        value={formData.password}
                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                        onBlur={() => setTouched({ ...touched, password: true })}
                      />
                      <InputRightElement>
                        <IconButton
                          variant="ghost" size="sm" aria-label="toggle"
                          icon={showPassword ? <FiEyeOff /> : <FiEye />}
                          onClick={() => setShowPassword(!showPassword)}
                        />
                      </InputRightElement>
                    </InputGroup>
                    <FormErrorMessage>{errors.password}</FormErrorMessage>
                  </FormControl>

                  <Checkbox
                    isChecked={formData.remember_me}
                    onChange={(e) => setFormData({ ...formData, remember_me: e.target.checked })}
                    colorScheme="pink"
                  >
                    记住我（7 天免登录）
                  </Checkbox>

                  {error && (
                    <Box w="full" p={3} borderRadius="md" bg="red.50" color="red.600"
                      fontSize="sm" textAlign="center">
                      {error}
                    </Box>
                  )}

                  <Button type="submit" colorScheme="brand" w="full" size="lg"
                    isLoading={isLoading} isDisabled={hasError}
                    leftIcon={<FiHeart />}>
                    登录
                  </Button>
                </VStack>
              </form>
            </CardBody>
          </Card>

          <Text color="gray.500">
            还没有账号？
            <Link to="/register">
              <Text as="span" color="brand.500" fontWeight={600} ml={1}>
                立即注册
              </Text>
            </Link>
          </Text>
        </VStack>
      </Container>
    </Box>
  )
}

export default Login
