/** API 配置 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const API_CONFIG = {
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 秒
  headers: {
    'Content-Type': 'application/json',
  },
};

