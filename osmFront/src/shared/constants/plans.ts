// src/constants/plans.ts
export const PLAN_LIMITS = {
    trial:      { max_users: 1,   max_branches: 1,  max_products: 200,    duration_days: 7,   price_month: 0,   price_year: 0 },
    basic:      { max_users: 5,   max_branches: 2,  max_products: 1000,   duration_days: 30,  price_month: 19,  price_year: 190 },
    premium:    { max_users: 50,  max_branches: 5,  max_products: 10000,  duration_days: 30,  price_month: 49,  price_year: 490 },
    enterprise: { max_users: 200, max_branches: 20, max_products: 100000, duration_days: 365, price_month: 99,  price_year: 990 }
  } as const;
  
  export type PlanName = keyof typeof PLAN_LIMITS;
  


