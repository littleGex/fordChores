<script setup>
import { formatEuro } from '../utils/format'
defineProps(['history']) // Receive the history array from DashboardView
</script>

<template>
  <div class="bg-white rounded-3xl border border-gray-100 overflow-hidden shadow-sm">
    <ul class="divide-y divide-gray-50">
      <li v-for="item in history" :key="item.id" class="p-5 hover:bg-gray-50/50 transition flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <div :class="[
            'w-12 h-12 rounded-2xl flex items-center justify-center',
            item.status === 'paid' ? 'bg-green-100 text-green-600' : 'bg-amber-100 text-amber-600'
          ]">
            <svg v-if="item.status === 'paid'" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p class="font-bold text-gray-800">{{ item.task }}</p>
            <p class="text-xs text-gray-400 font-medium">{{ item.date }}</p>
          </div>
        </div>

        <div class="text-right">
          <p class="font-black text-gray-900">{{ formatEuro(item.reward) }}</p>
          <span :class="[
            'text-[10px] uppercase tracking-widest font-black px-2 py-0.5 rounded-md',
            item.status === 'paid' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
          ]">
            {{ item.status }}
          </span>
        </div>
      </li>
    </ul>
    <div v-if="history.length === 0" class="p-10 text-center text-gray-400">
      No activity yet. Complete a chore to get started!
    </div>
  </div>
</template>
