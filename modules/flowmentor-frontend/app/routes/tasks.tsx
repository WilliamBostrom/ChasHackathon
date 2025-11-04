import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "~/components/ui/card";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Label } from "~/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "~/components/ui/select";
import { Badge } from "~/components/ui/badge";
import { apiMethods, type Task } from "~/lib/api";
import { Trash2, Plus, CheckCircle2, Circle } from "lucide-react";

export default function TasksPage() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [newTask, setNewTask] = useState({
    type: "todo" as "todo" | "gym" | "meeting",
    title: "",
    duration: "",
    time: "",
  });
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      const today = new Date().toISOString().split("T")[0];
      const data = await apiMethods.getTasks(today);
      setTasks(data);
    } catch (error) {
      console.error("Failed to load tasks:", error);
    }
  };

  const handleAddTask = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const taskData: Omit<Task, "id"> = {
        type: newTask.type,
        title: newTask.title,
        duration: newTask.duration ? parseInt(newTask.duration) : undefined,
        time: newTask.time || undefined,
        completed: false,
      };

      await apiMethods.addTask(taskData);
      await loadTasks();

      setNewTask({
        type: "todo",
        title: "",
        duration: "",
        time: "",
      });
    } catch (error) {
      console.error("Failed to add task:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleComplete = async (task: Task) => {
    try {
      await apiMethods.updateTask(task.id, { completed: !task.completed });
      await loadTasks();
    } catch (error) {
      console.error("Failed to update task:", error);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    try {
      await apiMethods.deleteTask(taskId);
      await loadTasks();
    } catch (error) {
      console.error("Failed to delete task:", error);
    }
  };

  const handleGeneratePlan = async () => {
    setIsLoading(true);
    try {
      const today = new Date().toISOString().split("T")[0];
      await apiMethods.generateDayPlan(today);
      navigate("/plan");
    } catch (error) {
      console.error("Failed to generate plan:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const getTaskIcon = (type: string) => {
    switch (type) {
      case "gym":
        return "💪";
      case "meeting":
        return "📅";
      default:
        return "✓";
    }
  };

  const getTaskColor = (type: string) => {
    switch (type) {
      case "gym":
        return "bg-green-100 text-green-800";
      case "meeting":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-purple-100 text-purple-800";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-100 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <Card className="shadow-xl">
          <CardHeader>
            <CardTitle className="text-3xl font-bold">
              Plan Your Day 📝
            </CardTitle>
            <CardDescription className="text-lg">
              Add tasks, gym sessions, and meetings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAddTask} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="type">Type</Label>
                  <Select
                    value={newTask.type}
                    onValueChange={(value: "todo" | "gym" | "meeting") =>
                      setNewTask({ ...newTask, type: value })
                    }
                  >
                    <SelectTrigger id="type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="todo">✓ To-Do</SelectItem>
                      <SelectItem value="gym">💪 Gym Session</SelectItem>
                      <SelectItem value="meeting">📅 Meeting</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="title">Title</Label>
                  <Input
                    id="title"
                    placeholder="What needs to be done?"
                    value={newTask.title}
                    onChange={(e) =>
                      setNewTask({ ...newTask, title: e.target.value })
                    }
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="duration">Duration (min)</Label>
                  <Input
                    id="duration"
                    type="number"
                    placeholder="30"
                    value={newTask.duration}
                    onChange={(e) =>
                      setNewTask({ ...newTask, duration: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="time">Time (optional)</Label>
                  <Input
                    id="time"
                    type="time"
                    value={newTask.time}
                    onChange={(e) =>
                      setNewTask({ ...newTask, time: e.target.value })
                    }
                  />
                </div>
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={isLoading || !newTask.title.trim()}
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Task
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card className="shadow-xl">
          <CardHeader>
            <CardTitle className="text-2xl">Your Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            {tasks.length === 0 ? (
              <p className="text-center text-gray-500 py-8">
                No tasks yet. Add your first task above!
              </p>
            ) : (
              <div className="space-y-3">
                {tasks.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center gap-3 p-4 rounded-lg border bg-white hover:shadow-md transition-shadow"
                  >
                    <button
                      onClick={() => handleToggleComplete(task)}
                      className="flex-shrink-0"
                    >
                      {task.completed ? (
                        <CheckCircle2 className="h-6 w-6 text-green-500" />
                      ) : (
                        <Circle className="h-6 w-6 text-gray-300" />
                      )}
                    </button>

                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-lg">
                          {getTaskIcon(task.type)}
                        </span>
                        <h3
                          className={`font-semibold ${
                            task.completed
                              ? "line-through text-gray-400"
                              : "text-gray-800"
                          }`}
                        >
                          {task.title}
                        </h3>
                        <Badge className={getTaskColor(task.type)}>
                          {task.type}
                        </Badge>
                      </div>
                      <div className="text-sm text-gray-500">
                        {task.duration && <span>{task.duration} min</span>}
                        {task.time && task.duration && <span> • </span>}
                        {task.time && <span>{task.time}</span>}
                      </div>
                    </div>

                    <button
                      onClick={() => handleDeleteTask(task.id)}
                      className="flex-shrink-0 text-red-500 hover:text-red-700"
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Button
          onClick={handleGeneratePlan}
          size="lg"
          className="w-full text-lg py-6"
          disabled={isLoading || tasks.length === 0}
        >
          {isLoading ? "Generating..." : "Generate AI Day Plan 🤖"}
        </Button>
      </div>
    </div>
  );
}
