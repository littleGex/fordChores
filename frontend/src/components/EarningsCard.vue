<script setup>
import axios from 'axios' // 1. Added missing axios import
import {formatEuro} from '../utils/format'

const props = defineProps(['balance', 'userId'])
const emit = defineEmits(['paid']) // 2. Explicitly define the emit

const requestPayment = async () => {
  if (props.balance <= 0) {
    alert("You don't have any pending earnings to request!")
    return
  }

  try {
    const API = import.meta.env.VITE_API_URL || 'http://localhost:5001/api/v1'
    // Capture the response here
    const res = await axios.post(`${API}/users/${props.userId}/request_payout`)

    // Now res.data.email_status will be accessible
    if (res?.data?.email_status === 'sent') {
      alert(`Great job! Your request for ${formatEuro(props.balance)} has been sent. Check your email for the itemized list!`)
    } else {
      alert("Payout processed! (Email status: " + (res?.data?.email_status || 'unknown') + ")")
    }

    emit('paid')
  } catch (err) {
    console.error("Payout failed:", err)
    alert("An error occurred while processing your payout.")
  }
}
</script>

<template>
  <div
    class="bg-indigo-600 rounded-3xl p-8 text-white flex flex-col md:flex-row justify-between items-center gap-6 shadow-xl shadow-indigo-100">
    <div class="flex items-center space-x-6">
      <div class="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" fill="none"
             viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"/>
        </svg>
      </div>
      <div>
        <p class="text-indigo-100 text-sm font-medium uppercase tracking-wider">Pending Balance</p>
        <h2 class="text-6xl font-black">{{ formatEuro(balance) }}</h2>
      </div>
    </div>

    <button
      @click="requestPayment"
      class="bg-white text-indigo-600 px-8 py-4 rounded-2xl font-bold shadow-lg hover:bg-indigo-50 transition active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
      :disabled="balance <= 0"
    >
      Request Payout
    </button>
  </div>
</template>
