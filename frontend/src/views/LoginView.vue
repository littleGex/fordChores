<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { AUTH_URL, ALLOWED_ROLES, setSession } from '../auth'

const router = useRouter()
const users = ref([])
const selectedUserId = ref(null)
const password = ref('')
const errorMessage = ref('')
const loading = ref(false)

const fetchUsers = async () => {
  try {
    // Parents and children; other adults aren't part of the chore tracker
    const res = await axios.get(`${AUTH_URL}/login-options`, { params: { audience: 'household' } })
    users.value = res.data
  } catch {
    errorMessage.value = 'Could not load the family list. Please try again.'
  }
}

const submit = async () => {
  if (!selectedUserId.value || !password.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await axios.post(`${AUTH_URL}/login`, {
      user_id: selectedUserId.value,
      password: password.value,
    })
    if (!ALLOWED_ROLES.includes(res.data.user.role)) {
      errorMessage.value = 'This login cannot use the chore tracker.'
      return
    }
    setSession(res.data.access_token, res.data.user)
    router.push('/dashboard')
  } catch (e) {
    // 403 and 429 carry the reason, e.g. an account still waiting for
    // approval, or too many wrong passwords
    if (e.response?.status === 401) {
      errorMessage.value = 'Wrong password!'
    } else if ([403, 429].includes(e.response?.status)) {
      errorMessage.value = e.response.data.detail
    } else {
      errorMessage.value = 'Login failed. Please try again.'
    }
  } finally {
    password.value = ''
    loading.value = false
  }
}

onMounted(fetchUsers)
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-600 to-purple-700 px-4">
    <div class="max-w-md w-full text-center p-10 bg-white/10 backdrop-blur-lg rounded-3xl border border-white/20 shadow-2xl">
      <h1 class="text-4xl font-black text-white mb-2">ChoreTracker</h1>
      <p class="text-indigo-100 mb-8">Who are you?</p>

      <div class="grid grid-cols-2 gap-3 mb-6">
        <button
          v-for="u in users"
          :key="u.id"
          @click="selectedUserId = u.id"
          :class="[
            'py-3 rounded-xl font-bold transition-all',
            selectedUserId === u.id ? 'bg-white text-indigo-600 shadow-lg' : 'bg-white/20 text-white hover:bg-white/30',
          ]"
        >
          {{ u.display_name }}
        </button>
      </div>

      <form v-if="selectedUserId" @submit.prevent="submit" class="space-y-3">
        <input
          v-model="password"
          type="password"
          placeholder="Password"
          autocomplete="current-password"
          class="w-full px-4 py-3 rounded-xl border-none outline-none font-medium text-gray-900 bg-white"
        />
        <button
          type="submit"
          :disabled="loading || !password"
          class="w-full py-4 bg-white text-indigo-600 font-bold rounded-xl shadow-lg hover:bg-indigo-50 disabled:opacity-60"
        >
          Log in
        </button>
      </form>

      <p v-if="errorMessage" class="text-white font-bold mt-4 bg-red-500/60 rounded-xl py-2 px-3">{{ errorMessage }}</p>
    </div>
  </div>
</template>
