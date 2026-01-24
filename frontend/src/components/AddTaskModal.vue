<script setup>
import {ref} from 'vue'
import axios from 'axios'
import {formatEuro} from '../utils/format'

const emit = defineEmits(['close', 'taskAdded'])

// Form State
const task = ref('')
const reward = ref(2.00)
const isSubmitting = ref(false)

const submitTask = async () => {
  if (!task.value || reward.value <= 0) return

  isSubmitting.value = true
  try {
    const API = import.meta.env.VITE_API_URL || 'http://localhost:5001/api/v1'
    // CHANGE THESE KEYS:
    await axios.post(`${API}/chores/`, {
      task_name: task.value,    // Changed from 'task'
      reward_level: reward.value // Changed from 'reward'
    })

    emit('taskAdded')
    emit('close')

    task.value = ''
    reward.value = 2.00
  } catch (err) {
    console.error("Failed to add task:", err)
    alert("Could not save task. Please check if the backend is running.")
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div
    class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">

    <div
      class="bg-white w-full max-w-md rounded-[2.5rem] p-8 shadow-2xl transform transition-all border border-gray-100">

      <div class="flex justify-between items-center mb-8">
        <div class="flex items-center space-x-3">
          <div class="bg-indigo-100 p-2 rounded-xl text-indigo-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24"
                 stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
            </svg>
          </div>
          <h2 class="text-2xl font-black text-gray-800 tracking-tight">New Chore</h2>
        </div>

        <button @click="$emit('close')"
                class="p-2 hover:bg-gray-100 rounded-full text-gray-400 transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24"
               stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <div class="space-y-6">
        <div>
          <label class="block text-xs font-black text-gray-400 uppercase tracking-widest mb-2 ml-1">Task
            Description</label>
          <input
            v-model="task"
            type="text"
            placeholder="e.g. Empty the dishwasher"
            class="w-full px-5 py-4 bg-gray-50 border border-gray-100 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:bg-white outline-none transition-all font-medium text-gray-700"
          />
        </div>

        <div>
          <label class="block text-xs font-black text-gray-400 uppercase tracking-widest mb-2 ml-1">Reward
            Value</label>
          <div class="relative">
            <input
              v-model="reward"
              type="number"
              step="0.50"
              class="w-full pl-5 pr-14 py-4 bg-gray-50 border border-gray-100 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:bg-white outline-none transition-all font-bold text-gray-800 text-lg"
            />
            <span class="absolute right-5 top-4 text-gray-400 font-bold text-xl">€</span>
          </div>
          <p class="mt-2 text-xs text-gray-400 ml-1">
            Suggested for this task: <span class="text-indigo-500 font-bold">{{
              formatEuro(reward)
            }}</span>
          </p>
        </div>

        <button
          @click="submitTask"
          :disabled="isSubmitting || !task"
          class="w-full py-4 bg-indigo-600 text-white font-black rounded-2xl shadow-lg shadow-indigo-100 hover:bg-indigo-700 hover:shadow-indigo-200 transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
        >
          <span v-if="isSubmitting">Saving...</span>
          <template v-else>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20"
                 fill="currentColor">
              <path fill-rule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z"
                    clip-rule="evenodd"/>
            </svg>
            <span>Create Task</span>
          </template>
        </button>
      </div>

    </div>
  </div>
</template>
