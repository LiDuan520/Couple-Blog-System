/**
 * 主题：粉紫少女风
 *
 * 主色 #FF6B9D (粉) + #C44569 (玫红)
 * 辅色 #B983FF (紫) + #94D0FF (淡蓝)
 * 渐变背景：linear-gradient(135deg, #FFE0EC 0%, #F5E1FF 50%, #E1F0FF 100%)
 */
import { extendTheme } from '@chakra-ui/react'

const theme = extendTheme({
  config: {
    initialColorMode: 'light',
    useSystemColorMode: false,
  },
  colors: {
    brand: {
      50: '#FFF0F6',
      100: '#FFE0EC',
      200: '#FFC2D9',
      300: '#FFA1BF',
      400: '#FF7BA8',
      500: '#FF6B9D',  // 主粉
      600: '#E84A85',
      700: '#C44569',  // 玫红
      800: '#9C2E4D',
      900: '#741C36',
    },
    purple: {
      50: '#F5E1FF',
      100: '#E6CCFF',
      200: '#D1A8FF',
      300: '#B983FF',  // 紫
      400: '#9B5DFF',
      500: '#7E3AED',
      600: '#6422D6',
      700: '#4F1AA8',
      800: '#3A1378',
      900: '#260B4D',
    },
    cream: {
      50: '#FFFBF7',
      100: '#FFF5EB',
    },
  },
  fonts: {
    heading: `"PingFang SC", "Microsoft YaHei", -apple-system, BlinkMacSystemFont, sans-serif`,
    body: `"PingFang SC", "Microsoft YaHei", -apple-system, BlinkMacSystemFont, sans-serif`,
  },
  styles: {
    global: {
      'html, body, #root': {
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #FFE0EC 0%, #F5E1FF 50%, #E1F0FF 100%)',
        backgroundAttachment: 'fixed',
        color: '#2D1B36',
      },
      '*::-webkit-scrollbar': {
        width: '8px',
        height: '8px',
      },
      '*::-webkit-scrollbar-thumb': {
        background: 'rgba(255, 107, 157, 0.4)',
        borderRadius: '4px',
      },
      '*::-webkit-scrollbar-track': {
        background: 'transparent',
      },
    },
  },
  components: {
    Button: {
      baseStyle: {
        fontWeight: 600,
        borderRadius: 'full',
        transition: 'all 0.2s',
      },
      variants: {
        solid: (props) => ({
          bg: props.colorScheme === 'brand'
            ? 'linear-gradient(135deg, #FF6B9D 0%, #C44569 100%)'
            : undefined,
          color: 'white',
          boxShadow: '0 4px 14px rgba(255, 107, 157, 0.35)',
          _hover: {
            transform: 'translateY(-1px)',
            boxShadow: '0 6px 20px rgba(255, 107, 157, 0.5)',
            _disabled: { transform: 'none' },
          },
          _active: { transform: 'translateY(0)' },
        }),
        ghost: {
          color: 'brand.500',
          _hover: { bg: 'brand.50' },
        },
        outline: {
          borderColor: 'brand.300',
          color: 'brand.600',
          _hover: { bg: 'brand.50' },
        },
      },
    },
    Card: {
      baseStyle: {
        container: {
          borderRadius: '20px',
          background: 'rgba(255, 255, 255, 0.85)',
          backdropFilter: 'blur(12px)',
          boxShadow: '0 8px 32px rgba(196, 69, 105, 0.12)',
          border: '1px solid rgba(255, 255, 255, 0.6)',
        },
      },
    },
    Heading: {
      baseStyle: {
        color: 'brand.700',
      },
    },
    Badge: {
      baseStyle: {
        borderRadius: 'full',
        px: 2,
        py: 0.5,
        fontWeight: 600,
      },
    },
    Input: {
      variants: {
        outline: {
          field: {
            borderRadius: '12px',
            borderColor: 'brand.200',
            bg: 'rgba(255, 255, 255, 0.8)',
            _hover: { borderColor: 'brand.300' },
            _focus: {
              borderColor: 'brand.500',
              boxShadow: '0 0 0 1px #FF6B9D',
            },
          },
        },
      },
      defaultProps: { variant: 'outline' },
    },
    Textarea: {
      variants: {
        outline: {
          borderRadius: '12px',
          borderColor: 'brand.200',
          bg: 'rgba(255, 255, 255, 0.8)',
          _hover: { borderColor: 'brand.300' },
          _focus: {
            borderColor: 'brand.500',
            boxShadow: '0 0 0 1px #FF6B9D',
          },
        },
      },
      defaultProps: { variant: 'outline' },
    },
    Select: {
      variants: {
        outline: {
          field: {
            borderRadius: '12px',
            borderColor: 'brand.200',
            bg: 'rgba(255, 255, 255, 0.8)',
          },
        },
      },
      defaultProps: { variant: 'outline' },
    },
  },
})

export default theme
