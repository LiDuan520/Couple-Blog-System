/**
 * 加载 / 空状态
 */
import { Box, Spinner, VStack, Text, Button } from '@chakra-ui/react'

export function LoadingState({ label = '加载中...' }) {
  return (
    <VStack py={12} spacing={3}>
      <Spinner size="lg" thickness="3px" speed="0.8s"
        color="brand.400" />
      <Text color="gray.500" fontSize="sm">{label}</Text>
    </VStack>
  )
}

export function EmptyState({ icon = '💭', title, description, actionLabel, onAction }) {
  return (
    <VStack py={16} spacing={3}>
      <Text fontSize="6xl" lineHeight={1}>{icon}</Text>
      <Text fontWeight={700} fontSize="lg" color="gray.600">{title}</Text>
      {description && (
        <Text color="gray.400" fontSize="sm" maxW="md" textAlign="center">
          {description}
        </Text>
      )}
      {actionLabel && (
        <Button mt={2} colorScheme="brand" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </VStack>
  )
}
