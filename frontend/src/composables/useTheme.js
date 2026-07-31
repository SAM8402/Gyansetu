import { ref } from 'vue'

const isDark = ref(false)

export function useTheme() {
  function applyTheme() {
    if (isDark.value) {
      document.documentElement.classList.add('dark')
      document.body.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      document.body.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }

  function toggleTheme() {
    isDark.value = !isDark.value
    applyTheme()
  }

  function initTheme() {
    const saved = localStorage.getItem('theme')
    if (saved) {
      isDark.value = saved === 'dark'
    } else {
      isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    applyTheme()
  }

  return {
    isDark,
    toggleTheme,
    initTheme,
  }
}
