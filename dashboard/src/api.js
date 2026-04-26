import axios from "axios";

const api = axios.create({ baseURL: "https://balans-production.up.railway.app" });

export const getKPI          = ()       => api.get("/summary/kpi").then(r => r.data);
export const getMonthly      = ()       => api.get("/summary/month").then(r => r.data);
export const getCategories   = ()       => api.get("/summary/categories").then(r => r.data);
export const getTransactions = (params) => api.get("/transactions", { params }).then(r => r.data);
export const addTransaction  = (data)   => api.post("/transactions", data).then(r => r.data);
export const updateTransaction = (id, data) => api.put(`/transactions/${id}`, data).then(r => r.data);
export const deleteTransaction = (id)   => api.delete(`/transactions/${id}`).then(r => r.data);
