import { reactive, computed } from 'vue'

// Logins are the family accounts kept by the fordDbs API (shared with
// Fordstagram and Pocket Money); the chore tracker has none of its own
export const AUTH_URL = import.meta.env.VITE_AUTH_URL || 'http://localhost:8005/v1/family-photos'

// Pocket Money lives next to the logins on the same API
export const POCKET_MONEY_URL = AUTH_URL.replace(/\/family-photos\/?$/, '/pocket-money')

const PARENT_ROLES = ['parent', 'admin']
// Adults outside the household aren't part of the chore tracker
export const ALLOWED_ROLES = [...PARENT_ROLES, 'child']

const readUser = () => {
  try {
    return JSON.parse(localStorage.getItem('user'))
  } catch {
    return null
  }
}

export const auth = reactive({
  token: localStorage.getItem('token'),
  user: readUser(),
})

export const isLoggedIn = computed(() => !!auth.token && !!auth.user)
export const isParent = computed(() => isLoggedIn.value && PARENT_ROLES.includes(auth.user.role))

export const setSession = (token, user) => {
  auth.token = token
  auth.user = user
  localStorage.setItem('token', token)
  localStorage.setItem('user', JSON.stringify(user))
}

export const setToken = (token) => {
  auth.token = token
  localStorage.setItem('token', token)
}

export const logout = () => {
  auth.token = null
  auth.user = null
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}
