<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { formatEuro } from '../utils/format'

const users = ref([])
const newUserName = ref('')
const newUserEmail = ref('')
const API = import.meta.env.VITE_API_URL || 'http://localhost:5001/api/v1'

const loadUsers = async () => {
  try {
    const res = await axios.get(`${API}/users/`)
    users.value = res.data
  } catch (err) {
    console.error("Failed to load users:", err)
  }
}

const addUser = async () => {
  if (!newUserName.value || !newUserEmail.value) {
    alert("Please enter both a name and an email.")
    return
  }

  try {
    await axios.post(`${API}/users/add_user`, {
      name: newUserName.value,
      email: newUserEmail.value
    })

    newUserName.value = ''
    newUserEmail.value = ''
    loadUsers()
  } catch (err) {
    console.error("Failed to add user:", err)
    alert("Error adding member. Ensure the email is unique.")
  }
}

onMounted(loadUsers)
</script>

<template>
  <div class="max-w-3xl mx-auto p-8">

    <router-link
      to="/dashboard"
      class="inline-flex items-center text-sm font-bold text-indigo-600 hover:text-indigo-800 transition-colors mb-6 group"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2 transform group-hover:-translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
      </svg>
      Back to Dashboard
    </router-link>

    <div class="mb-10">
      <h2 class="text-3xl font-black text-gray-900">Family Members</h2>
      <p class="text-gray-500 font-medium">Add and manage who can track chores.</p>
    </div>

    <div class="bg-white p-8 rounded-[2.5rem] border border-gray-100 shadow-sm mb-12">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div class="space-y-2">
          <label class="text-xs font-black uppercase tracking-widest text-gray-400 ml-1">Name</label>
          <input
            v-model="newUserName"
            type="text"
            placeholder="e.g. Maya"
            class="w-full px-5 py-4 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500 border border-transparent focus:bg-white transition-all font-bold"
          />
        </div>
        <div class="space-y-2">
          <label class="text-xs font-black uppercase tracking-widest text-gray-400 ml-1">Email Address</label>
          <input
            v-model="newUserEmail"
            type="email"
            placeholder="maya@example.com"
            class="w-full px-5 py-4 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500 border border-transparent focus:bg-white transition-all font-bold"
          />
        </div>
      </div>

      <button
        @click="addUser"
        class="w-full bg-indigo-600 text-white px-6 py-4 rounded-2xl font-black shadow-lg shadow-indigo-100 hover:bg-indigo-700 hover:shadow-indigo-200 transition-all active:scale-[0.98]"
      >
        Add Family Member
      </button>
    </div>

    <div class="space-y-4">
      <h3 class="text-sm font-black uppercase tracking-widest text-gray-400 ml-1">Current Members</h3>
      <div v-for="user in users" :key="user.id"
           class="bg-white p-6 rounded-3xl border border-gray-100 flex justify-between items-center hover:shadow-md transition-shadow">
        <div class="flex items-center space-x-5">
          <div class="w-14 h-14 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center font-black text-xl">
            {{ user.name.charAt(0) }}
          </div>
          <div>
            <p class="font-black text-gray-900 text-lg">{{ user.name }}</p>
            <p class="text-sm text-gray-400 font-medium">{{ user.email }}</p>
          </div>
        </div>

        <div class="text-right">
          <div class="px-3 py-1 bg-gray-50 rounded-lg text-[10px] font-black uppercase tracking-wider text-gray-400">
            Member
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
