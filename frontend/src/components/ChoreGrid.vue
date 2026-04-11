<script setup>
import {ref} from "vue"
import axios from 'axios'
import {formatEuro} from '../utils/format'

const props = defineProps(['chores', 'userId'])
const emit = defineEmits(['taskCompleted'])
const API = import.meta.env.VITE_API_URL || 'http://localhost:5001/api/v1'
const processingIds = ref(new Set())

const completeTask = async (choreId) => {
  if (processingIds.value.has(choreId)) return

  try {
    processingIds.value.add(choreId)  // Set loading state
    await axios.post(`${API}/chores/complete`, {
      user_id: props.userId,
      chore_id: choreId
    })
    emit('taskCompleted')
  } catch (err) {
    console.error("Completion failed:", err)
  } finally {
    processingIds.value.delete(choreId)  // remove loading state
  }
}
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div v-for="chore in chores" :key="chore.id"
         class="bg-white p-6 rounded-[2rem] border border-gray-100 shadow-sm">
      <div class="flex justify-between items-start mb-6">
        <h4 class="font-black text-gray-900 text-lg">{{ chore.task }}</h4>
        <span class="text-indigo-600 font-black bg-indigo-50 px-3 py-1 rounded-xl text-sm">
          {{ formatEuro(chore.reward) }}
        </span>
      </div>
      <button
        @click="completeTask(chore.id)"
        :disabled="processingIds.has(chore.id)"
        :class="[
          'w-full py-3 font-bold rounded-2xl transition-all active:scale-95',
          processingIds.has(chore.id)
            ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
            : 'bg-indigo-600 text-white active:bg-indigo-700'
        ]"
      >
        <span v-if="processingIds.has(chore.id)">Saving...</span>
        <span v-else>Complete</span>
      </button>
    </div>
  </div>
</template>
