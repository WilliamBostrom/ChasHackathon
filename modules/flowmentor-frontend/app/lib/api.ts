import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:3030";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log("🌐 API Request:", {
      method: config.method?.toUpperCase(),
      url: config.url,
      baseURL: config.baseURL,
      fullURL: `${config.baseURL}${config.url}`,
      data: config.data,
      params: config.params,
    });
    return config;
  },
  (error) => {
    console.error("❌ API Request Error:", error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log("✅ API Response:", {
      status: response.status,
      statusText: response.statusText,
      url: response.config.url,
      data: response.data,
    });
    return response;
  },
  (error) => {
    console.error("❌ API Response Error:", {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      data: error.response?.data,
    });
    return Promise.reject(error);
  }
);

// Types
export interface MorningCheckIn {
  feeling: string;
  focus: string;
  date: string;
}

export interface Task {
  id: string;
  type: "todo" | "gym" | "meeting";
  title: string;
  duration?: number;
  time?: string;
  completed?: boolean;
}

export interface FocusBlock {
  id: string;
  title: string;
  startTime: string;
  endTime: string;
  duration: number;
  type: "focus" | "break" | "routine";
}

export interface DayPlan {
  date: string;
  blocks: FocusBlock[];
  morningRoutine: string[];
  eveningRoutine: string[];
}

export interface AfternoonReflection {
  accomplishments: string;
  challenges: string;
  learnings: string;
  date: string;
}

export interface MicroGoal {
  id: string;
  title: string;
  description: string;
  aiReasoning: string;
}

export interface WeeklySummary {
  weekNumber: number;
  suggestedGoals: MicroGoal[];
  insights: string;
  completionRate: number;
}

// API Methods
export const apiMethods = {
  // Morning
  submitMorningCheckIn: async (data: MorningCheckIn) => {
    const response = await api.post("/morning-checkin", data);
    return response.data;
  },

  // Tasks
  addTask: async (task: Omit<Task, "id">) => {
    const response = await api.post("/tasks", task);
    return response.data;
  },

  getTasks: async (date: string) => {
    const response = await api.get(`/tasks?date=${date}`);
    return response.data;
  },

  updateTask: async (id: string, updates: Partial<Task>) => {
    const response = await api.patch(`/tasks/${id}`, updates);
    return response.data;
  },

  deleteTask: async (id: string) => {
    await api.delete(`/tasks/${id}`);
  },

  // AI Plan
  generateDayPlan: async (date: string) => {
    const response = await api.post("/generate-plan", { date });
    return response.data;
  },

  getDayPlan: async (date: string) => {
    const response = await api.get(`/plan?date=${date}`);
    return response.data;
  },

  // Focus Loop
  startFocusBlock: async (blockId: string) => {
    const response = await api.post(`/focus/${blockId}/start`);
    return response.data;
  },

  submitFocusFeedback: async (blockId: string, feedback: string) => {
    const response = await api.post(`/focus/${blockId}/feedback`, { feedback });
    return response.data;
  },

  // Afternoon
  submitAfternoonReflection: async (data: AfternoonReflection) => {
    const response = await api.post("/afternoon-reflection", data);
    return response.data;
  },

  getAISummary: async (date: string) => {
    const response = await api.get(`/ai-summary?date=${date}`);
    return response.data;
  },

  // Weekly
  getWeeklySummary: async (weekNumber: number) => {
    const response = await api.get(`/weekly-summary?week=${weekNumber}`);
    return response.data;
  },

  selectMicroGoal: async (goalId: string) => {
    const response = await api.post("/micro-goal/select", { goalId });
    return response.data;
  },
};
