<script setup>
defineProps(['users', 'activeId'])
defineEmits(['change'])
</script>

<template>
  <div class="flex bg-gray-100 p-1 rounded-xl shadow-inner border border-gray-200">
    <button
      v-for="user in users"
      :key="user.id"
      @click="$emit('change', user.id)"
      :class="[
        'flex-1 md:flex-none px-4 py-2 md:py-1.5 rounded-lg text-sm font-semibold transition-all duration-200',
        activeId === user.id
          ? 'bg-white text-indigo-600 shadow-sm'
          : 'text-gray-500 hover:text-gray-700'
      ]"
    >
      {{ user.name }}
    </button>
  </div>
</template>
