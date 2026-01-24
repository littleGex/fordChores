<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-600 to-purple-700 px-4">
    <div class="max-w-md w-full text-center p-10 bg-white/10 backdrop-blur-lg rounded-3xl border border-white/20 shadow-2xl">

      <div class="mx-auto w-20 h-20 bg-white rounded-2xl flex items-center justify-center shadow-lg mb-6">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
      </div>

      <h1 class="text-4xl font-black text-white mb-2">ChoreTracker</h1>
      <p class="text-indigo-100 mb-8">Helping families turn hard work into rewards.</p>

      <router-link
        to="/dashboard"
        class="inline-block w-full py-4 bg-white text-indigo-600 font-bold rounded-xl shadow-lg hover:bg-indigo-50 transition-transform hover:-translate-y-1"
      >
        Go to Dashboard
      </router-link>
    </div>
  </div>
</template>
