<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { formatEuro } from '../utils/format'

const users = ref([])
const chores = ref([])
const API = import.meta.env.VITE_API_URL || 'http://localhost:5001/api/v1'

const newUser = ref({ name: '', email: '' })

const loadData = async () => {
  try {
    const [uRes, cRes] = await Promise.all([
      axios.get(`${API}/users/`),
      axios.get(`${API}/chores/`)
    ])
    users.value = uRes.data
    chores.value = cRes.data
  } catch (err) { console.error("Admin load failed:", err) }
}

// --- USER ACTIONS ---

const addUser = async () => {
  if (!newUser.value.name || !newUser.value.email) return
  try {
    await axios.post(`${API}/users/add_user`, newUser.value) //
    newUser.value = { name: '', email: '' }
    loadData()
  } catch (err) { alert("Failed to add user.") }
}

const editUser = async (user) => {
  const name = prompt("Edit Name:", user.name)
  const email = prompt("Edit Email:", user.email)

  if (name && email) {
    try {
      // Uses PUT /api/v1/users/<id>
      await axios.put(`${API}/users/${user.id}`, { name, email })
      loadData()
    } catch (err) { alert("Failed to update user.") }
  }
}

const deleteUser = async (id) => {
  if (confirm("Remove family member?")) {
    await axios.delete(`${API}/users/${id}`) //
    loadData()
  }
}

// --- CHORE ACTIONS ---

const editChore = async (chore) => {
  const name = prompt("Task Name:", chore.task_name || chore.task)
  const reward = prompt("Reward (€):", chore.reward_level || chore.reward)
  if (name && reward) {
    await axios.put(`${API}/chores/${chore.id}`, { //
      task_name: name,
      reward_level: parseFloat(reward)
    })
    loadData()
  }
}

const deleteChore = async (id) => {
  if (confirm("Delete chore?")) {
    await axios.delete(`${API}/chores/${id}`) //
    loadData()
  }
}

onMounted(loadData)
</script>

<template>
  <div class="max-w-5xl mx-auto p-8">
    <router-link to="/dashboard" class="text-indigo-600 font-bold mb-12 inline-block group">
      <span class="inline-block transform group-hover:-translate-x-1 transition-transform">←</span>
      Back to Dashboard
    </router-link>

    <h2 class="text-4xl font-black mb-12 text-gray-900">Admin Control Center</h2>

    <section class="mb-16">
      <h3 class="text-xs font-black uppercase text-gray-400 tracking-widest mb-6">Family Management</h3>

      <div class="bg-indigo-50 p-6 rounded-[2rem] mb-6 flex gap-4 items-end">
        <div class="flex-1">
          <label class="block text-[10px] font-black text-indigo-400 uppercase mb-2">New Member Name</label>
          <input v-model="newUser.name" type="text" class="w-full px-4 py-3 rounded-xl border-none outline-none font-medium" />
        </div>
        <div class="flex-1">
          <label class="block text-[10px] font-black text-indigo-400 uppercase mb-2">Email Address</label>
          <input v-model="newUser.email" type="email" class="w-full px-4 py-3 rounded-xl border-none outline-none font-medium" />
        </div>
        <button @click="addUser" class="bg-indigo-600 text-white px-8 py-3 rounded-xl font-black text-sm hover:bg-indigo-700">Add</button>
      </div>

      <div v-for="user in users" :key="user.id" class="bg-white p-6 rounded-[2rem] border border-gray-100 mb-3 flex justify-between items-center shadow-sm">
        <div>
          <p class="font-bold text-gray-900">{{ user.name }}</p>
          <p class="text-xs text-gray-400 font-medium">{{ user.email }}</p>
        </div>
        <div class="flex space-x-6">
          <button @click="editUser(user)" class="text-indigo-600 font-bold text-sm">Edit</button>
          <button @click="deleteUser(user.id)" class="text-red-400 font-bold text-sm">Remove</button>
        </div>
      </div>
    </section>

    <section>
      <h3 class="text-xs font-black uppercase text-gray-400 tracking-widest mb-6">Chore Library</h3>
      <div v-for="chore in chores" :key="chore.id" class="bg-white p-6 rounded-[2rem] border border-gray-100 mb-3 flex justify-between items-center shadow-sm">
        <div>
          <p class="font-bold text-gray-900">{{ chore.task_name || chore.task }}</p>
          <p class="text-indigo-600 font-black text-sm">{{ formatEuro(chore.reward_level || chore.reward) }}</p>
        </div>
        <div class="flex space-x-6">
          <button @click="editChore(chore)" class="text-indigo-600 font-bold text-sm">Edit</button>
          <button @click="deleteChore(chore.id)" class="text-red-400 font-bold text-sm">Delete</button>
        </div>
      </div>
    </section>
  </div>
</template>
