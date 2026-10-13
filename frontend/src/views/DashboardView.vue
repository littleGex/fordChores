<script setup>
import { ref, onMounted, watch } from 'vue'
import axios from '../api'
import { useRouter } from 'vue-router'
import { auth, isParent, logout as clearSession } from '../auth'

// Component Imports
import UserToggle from '../components/UserToggle.vue'
import EarningsCard from '../components/EarningsCard.vue'
import ChoreGrid from '../components/ChoreGrid.vue'
import HistoryTimeline from '../components/HistoryTimeline.vue'
import AddTaskModal from "../components/AddTaskModal.vue"

const router = useRouter()
const activeUserId = ref(1)
const users = ref([])
const chores = ref([])
const balance = ref(0)
const history = ref([])
const loading = ref(true)
const showAddTask = ref(false)

const API = import.meta.env.VITE_API_URL || 'http://localhost:5001/api/v1'

const logout = () => {
  clearSession()
  router.push('/login')
}

const loadDashboard = async () => {
  loading.value = true
  try {
    // A child's list only holds themselves, so make sure the selected
    // user is one this login may see before asking for their data
    const uRes = await axios.get(`${API}/users/`)
    users.value = uRes.data
    if (!users.value.some(u => u.id === activeUserId.value)) {
      if (users.value.length === 0) return
      activeUserId.value = users.value[0].id
      return // the watcher reloads for the new user
    }

    const [cRes, bRes, hRes] = await Promise.all([
      axios.get(`${API}/chores/`),
      axios.get(`${API}/users/${activeUserId.value}/balance`),
      axios.get(`${API}/users/${activeUserId.value}/history`)
    ])

    // Map backend keys to frontend names (task/reward)
    chores.value = cRes.data.map(c => ({
      ...c,
      task: c.task_name || c.task,
      reward: c.reward_level || c.reward
    }))
    balance.value = bRes.data.pending_balance
    history.value = hRes.data
  } catch (err) {
    console.error("Dashboard failed to load:", err)
  } finally {
    loading.value = false
  }
}

watch(activeUserId, loadDashboard)
onMounted(loadDashboard)
</script>

<template>
  <div class="min-h-screen bg-gray-50 pb-20">
    <header class="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <!-- One row on a wide screen. On a phone the user switcher drops
           to its own full-width row so nothing is squeezed or cut off. -->
      <div class="max-w-5xl mx-auto px-4 py-2 min-h-16 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <div class="flex items-center justify-between flex-1 md:flex-none md:justify-start md:space-x-8">
          <div class="font-black text-xl text-indigo-600 tracking-tighter select-none">
            ChoreTracker
          </div>

          <nav class="flex items-center space-x-1 md:space-x-4 text-sm font-bold text-gray-500 whitespace-nowrap">
            <button v-if="isParent" @click="showAddTask = true" class="px-2 py-2.5 hover:text-indigo-600 transition flex items-center">
              <span class="text-lg leading-none mr-1">+</span> Task
            </button>
            <router-link v-if="isParent" to="/admin" class="px-2 py-2.5 hover:text-indigo-600 transition">Admin</router-link>
            <button @click="logout" class="px-2 py-2.5 hover:text-indigo-600 transition">Log out</button>
            </nav>
        </div>

        <UserToggle
          v-if="users.length > 1"
          class="w-full md:w-auto"
          :users="users"
          :activeId="activeUserId"
          @change="(id) => activeUserId = id"
        />
        <span v-else-if="users.length === 1" class="text-sm font-semibold text-indigo-600 bg-indigo-50 px-3 py-1.5 rounded-lg">
          {{ users[0].name }}
        </span>
      </div>
    </header>

    <main class="max-w-5xl mx-auto px-4 py-6 md:py-8 space-y-8 md:space-y-10">
      <div v-if="loading" class="flex flex-col items-center justify-center py-20 text-gray-400 space-y-4">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
        <p class="font-medium">Syncing...</p>
      </div>

      <div v-else-if="users.length === 0" class="text-center py-20 text-gray-400 font-medium">
        No chore profile is linked to {{ auth.user.display_name }}'s login yet.
      </div>

      <template v-else>
        <EarningsCard :balance="balance" :userId="activeUserId" @paid="loadDashboard" />
        <section>
          <h3 class="text-xl font-black text-gray-900 mb-4 md:mb-6 flex items-center"><span class="mr-3 text-2xl">⚡</span> Available Chores</h3>
          <ChoreGrid :chores="chores" :userId="activeUserId" @taskCompleted="loadDashboard" />
        </section>
        <section>
          <h3 class="text-xl font-black text-gray-900 mb-4 md:mb-6 flex items-center"><span class="mr-3 text-2xl">🕒</span> Recent Activity</h3>
          <HistoryTimeline :history="history" />
        </section>
      </template>
    </main>

    <AddTaskModal v-if="showAddTask" @close="showAddTask = false" @taskAdded="loadDashboard" />
  </div>
</template>
