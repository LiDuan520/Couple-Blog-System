/**
 * 页面容器
 */
import { Box, Container, Heading, Text, HStack } from '@chakra-ui/react'

export default function PageContainer({
  title, subtitle, actions, children, maxW = '6xl',
}) {
  return (
    <Container maxW={maxW} px={0}>
      {(title || actions) && (
        <HStack justify="space-between" align="flex-end" mb={6} flexWrap="wrap" gap={3}>
          <Box>
            {title && (
              <Heading size="lg" mb={1}
                bgGradient="linear(to-r, brand.500, purple.500)"
                bgClip="text">
                {title}
              </Heading>
            )}
            {subtitle && <Text color="gray.500">{subtitle}</Text>}
          </Box>
          {actions && <HStack spacing={2}>{actions}</HStack>}
        </HStack>
      )}
      <Box>{children}</Box>
    </Container>
  )
}
