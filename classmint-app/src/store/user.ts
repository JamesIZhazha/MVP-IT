import { defineStore } from 'pinia'

export const useUser = defineStore('user', {
  state: () => ({ 
    user_id: 0, 
    username: '',
    balance: 0,
    recent: [] as any[]
  }),
  actions: { 
    set(u: { user_id: number; username: string }) { 
      this.user_id = u.user_id; 
      this.username = u.username 
    },
    updateBalance(balance: number, recent: any[] = []) {
      this.balance = balance
      if (recent.length > 0) {
        this.recent = recent
      }
    },
    clear() {
      this.user_id = 0
      this.username = ''
      this.balance = 0
      this.recent = []
    }
  }
})