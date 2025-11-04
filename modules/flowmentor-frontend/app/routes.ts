import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/home.tsx"),
  route("/morning", "routes/morning.tsx"),
  route("/tasks", "routes/tasks.tsx"),
  route("/plan", "routes/plan.tsx"),
  route("/focus/:blockId", "routes/focus.$blockId.tsx"),
  route("/afternoon", "routes/afternoon.tsx"),
  route("/weekly", "routes/weekly.tsx"),
] satisfies RouteConfig;
