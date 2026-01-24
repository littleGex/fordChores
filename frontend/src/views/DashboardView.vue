<script setup>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

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

const enterAdminMode = () => {
  const pin = prompt("Enter Parent PIN:")
  if (pin === '1234') {
    router.push('/admin')
  } else if (pin !== null) {
    alert("Incorrect PIN")
  }
}

const loadDashboard = async () => {
  loading.value = true
  try {
    const [uRes, cRes, bRes, hRes] = await Promise.all([
      axios.get(`${API}/users/`),
      axios.get(`${API}/chores/`),
      axios.get(`${API}/users/${activeUserId.value}/balance`),
      axios.get(`${API}/users/${activeUserId.value}/history`)
    ])

    users.value = uRes.data
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
      <div class="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
        <div class="flex items-center space-x-8">
          <div @click="enterAdminMode" class="font-black text-xl text-indigo-600 tracking-tighter cursor-pointer select-none">
            ChoreTracker
          </div>

          <nav class="flex items-center space-x-6 text-sm font-bold text-gray-500">
            <button @click="showAddTask = true" class="hover:text-indigo-600 transition flex items-center">
              <span class="text-lg mr-1">+</span> Add Task
            </button>
            </nav>
        </div>

        <UserToggle :users="users" :activeId="activeUserId" @change="(id) => activeUserId = id" />
      </div>
    </header>

    <main class="max-w-5xl mx-auto px-4 py-8 space-y-10">
      <div v-if="loading" class="flex flex-col items-center justify-center py-20 text-gray-400 space-y-4">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
        <p class="font-medium">Syncing...</p>
      </div>

      <template v-else>
        <EarningsCard :balance="balance" :userId="activeUserId" @paid="loadDashboard" />
        <section>
          <h3 class="text-xl font-black text-gray-900 mb-6 flex items-center"><span class="mr-3 text-2xl">⚡</span> Available Chores</h3>
          <ChoreGrid :chores="chores" :userId="activeUserId" @taskCompleted="loadDashboard" />
        </section>
        <section>
          <h3 class="text-xl font-black text-gray-900 mb-6 flex items-center"><span class="mr-3 text-2xl">🕒</span> Recent Activity</h3>
          <HistoryTimeline :history="history" />
        </section>
      </template>
    </main>

    <AddTaskModal v-if="showAddTask" @close="showAddTask = false" @taskAdded="loadDashboard" />
  </div>
</template>
