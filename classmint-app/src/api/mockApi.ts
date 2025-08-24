import { db } from '../mock/db'
db.ensureInit()

export const api = {
  login:   async (u:string,p:string)=>{ const r=db.login(u,p); if(!r.ok) throw new Error('账号或密码错误'); return r },
  balance: async (user_id:number)=> db.balance(user_id),
  
  // 简化：直接调用数据库，数据库会处理所有令牌格式
  claim:   async (tokenData:any, user_id:number)=> {
    try {
      // 直接调用数据库处理，数据库会自动识别令牌格式
      const result = await db.claim(user_id, JSON.stringify(tokenData));
      console.log('令牌处理成功:', result);
      return result;
    } catch (error: any) {
      console.error('令牌处理失败:', error);
      throw new Error(error.message || '令牌验证失败');
    }
  },
  
  verify:  async ()=> db.verify(),
}