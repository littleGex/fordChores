<script setup>
import { formatEuro } from '../utils/format'

// Define the history prop so the Dashboard can pass data into this component
defineProps({
  history: {
    type: Array,
    default: () => []
  }
})
</script>

<template>
  <div class="bg-white rounded-3xl border border-gray-100 overflow-hidden shadow-sm">
    <ul v-if="history.length > 0" class="divide-y divide-gray-50">
      <li
        v-for="(item, index) in history"
        :key="index"
        class="p-5 flex justify-between items-center hover:bg-gray-50 transition-colors"
      >
        <div class="flex items-center space-x-4">
          <div
            class="w-10 h-10 rounded-xl flex items-center justify-center"
            :class="item.status === 'paid' ? 'bg-green-50 text-green-600' : 'bg-indigo-50 text-indigo-600'"
          >
            <svg v-if="item.status === 'paid'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>

          <div>
            <p class="font-bold text-gray-800">{{ item.task }}</p>
            <p class="text-xs text-gray-400 font-medium">
              {{ new Date(item.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) }}
            </p>
          </div>
        </div>

        <div class="text-right">
          <p class="font-black text-gray-900">{{ formatEuro(item.reward) }}</p>
          <span
            :class="[
              'text-[10px] uppercase tracking-widest font-black px-2 py-0.5 rounded-md',
              item.status === 'paid' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
            ]"
          >
            {{ item.status }}
          </span>
        </div>
      </li>
    </ul>

    <div v-else class="p-12 text-center">
      <div class="inline-flex items-center justify-center w-16 h-16 bg-gray-50 text-gray-300 rounded-full mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <p class="text-gray-400 font-medium italic">No chores completed yet. Time to get to work!</p>
    </div>
  </div>
</template>
