import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const activeUserId = ref(localStorage.getItem('userId') || 1)

  function setActiveUser(id) {
    activeUserId.value = id
    localStorage.setItem('userId', id)
  }

  return { activeUserId, setActiveUser }
})
