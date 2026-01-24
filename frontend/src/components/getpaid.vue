<script setup>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import UserToggle from '../components/UserToggle.vue'
import EarningsCard from '../components/EarningsCard.vue'
import ChoreGrid from '../components/ChoreGrid.vue'
import HistoryTimeline from '../components/HistoryTimeline.vue'

// State
const activeUserId = ref(1)
const users = ref([])
const chores = ref([])
const balance = ref(0)
const history = ref([])
const loading = ref(true)

// API Base URL
const API = import.meta.env.VITE_API_URL || 'http://localhost:5001/api/v1'

const loadDashboard = async () => {
  loading.value = true
  try {
    // Parallel fetch for speed
    const [uRes, cRes, bRes, hRes] = await Promise.all([
      axios.get(`${API}/users/`),
      axios.get(`${API}/chores/`),
      axios.get(`${API}/users/${activeUserId.value}/balance`),
      axios.get(`${API}/users/${activeUserId.value}/history`)
    ])

    users.value = uRes.data
    chores.value = cRes.data
    balance.value = bRes.data.pending_balance
    history.value = hRes.data
  } catch (err) {
    console.error("Dashboard failed to load:", err)
  } finally {
    loading.value = false
  }
}

// Reload data when active user changes
watch(activeUserId, loadDashboard)

onMounted(loadDashboard)
</script>

<template>
  <div class="min-h-screen bg-gray-50 pb-20">
    <header class="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div class="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
        <h1 class="font-bold text-xl text-indigo-600">ChoreTracker</h1>
        <UserToggle
          :users="users"
          :activeId="activeUserId"
          @change="(id) => activeUserId = id"
        />
      </div>
    </header>

    <main class="max-w-5xl mx-auto px-4 py-8 space-y-8">
      <div v-if="loading" class="text-center py-10 text-gray-400">Loading your chores...</div>

      <template v-else>
        <EarningsCard :balance="balance" :userId="activeUserId" @paid="loadDashboard" />

        <section>
          <h3 class="text-lg font-bold mb-4 flex items-center">
            <span class="mr-2">⚡</span> Available Chores
          </h3>
          <ChoreGrid :chores="chores" :userId="activeUserId" @taskCompleted="loadDashboard" />
        </section>

        <section>
          <h3 class="text-lg font-bold mb-4 flex items-center">
            <span class="mr-2">🕒</span> Recent Activity
          </h3>
          <HistoryTimeline :history="history" />
        </section>
      </template>
    </main>
  </div>
</template>
