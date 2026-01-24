<script setup>
import axios from 'axios'
import { formatEuro } from '../utils/format'

const props = defineProps(['chores', 'userId'])
const emit = defineEmits(['taskCompleted'])

const completeTask = async (choreId) => {
  try {
    await axios.post('http://127.0.0.1:5000/api/v1/chores/complete', {
      user_id: props.userId,
      chore_id: choreId
    })
    emit('taskCompleted')
  } catch (err) {
    console.error("Completion failed:", err)
  }
}
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div v-for="chore in chores" :key="chore.id" class="bg-white p-6 rounded-[2rem] border border-gray-100 shadow-sm">
      <div class="flex justify-between items-start mb-6">
        <h4 class="font-black text-gray-900 text-lg">{{ chore.task }}</h4>
        <span class="text-indigo-600 font-black bg-indigo-50 px-3 py-1 rounded-xl text-sm">
          {{ formatEuro(chore.reward) }}
        </span>
      </div>
      <button @click="completeTask(chore.id)" class="w-full py-3 bg-gray-50 hover:bg-indigo-600 hover:text-white text-gray-400 font-bold rounded-2xl transition-all">
        Complete
      </button>
    </div>
  </div>
</template>
