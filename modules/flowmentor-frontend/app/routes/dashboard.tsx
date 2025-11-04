import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import Header from "~/components/Header";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "~/components/ui/card";
import { Button } from "~/components/ui/button";
import { Badge } from "~/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "~/components/ui/dialog";
import { Input } from "~/components/ui/input";
import { Label } from "~/components/ui/label";
import { Textarea } from "~/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "~/components/ui/select";
import { Calendar } from "~/components/ui/calendar";
import { ScrollArea } from "~/components/ui/scroll-area";
import {
  apiMethods,
  type Task,
  type FocusBlock,
  type DayPlan,
} from "~/lib/api";
import {
  CheckCircle2,
  Circle,
  Clock,
  Calendar as CalendarIcon,
  Plus,
  Upload,
  Play,
  Coffee,
  Zap,
  ChevronLeft,
  ChevronRight,
  X,
} from "lucide-react";
import {
  format,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  isSameDay,
  isToday,
  isSameMonth,
  addMonths,
  subMonths,
} from "date-fns";

// Extended types for calendar events
interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  startTime: string;
  endTime: string;
  date: string;
  type: "task" | "focus" | "meeting" | "routine" | "imported";
  completed?: boolean;
  source?: "manual" | "ics";
}

interface DayEvents {
  date: string;
  events: CalendarEvent[];
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [tasks, setTasks] = useState<Task[]>([]);
  const [plan, setPlan] = useState<DayPlan | null>(null);
  const [calendarEvents, setCalendarEvents] = useState<
    Map<string, CalendarEvent[]>
  >(new Map());
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(
    new Date()
  );
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [isEventModalOpen, setIsEventModalOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(false);

  // New task form state
  const [newTask, setNewTask] = useState({
    type: "todo" as "todo" | "gym" | "meeting",
    title: "",
    description: "",
    duration: "",
    time: "",
    date: format(new Date(), "yyyy-MM-dd"),
  });

  useEffect(() => {
    loadTodayData();
    loadCalendarEvents();
  }, []);

  useEffect(() => {
    loadCalendarEvents();
  }, [currentDate]);

  const loadTodayData = async () => {
    try {
      const today = new Date().toISOString().split("T")[0];

      // Load tasks
      const tasksData = await apiMethods.getTasks(today);
      setTasks(tasksData);

      // Try to load plan
      try {
        const planData = await apiMethods.getDayPlan(today);
        setPlan(planData);
      } catch (error) {
        console.log("No plan available yet");
      }
    } catch (error) {
      console.error("Failed to load today's data:", error);
    }
  };

  const loadCalendarEvents = async () => {
    // In a real app, this would fetch events for the month
    // For now, we'll construct events from tasks and plan
    const start = startOfMonth(currentDate);
    const end = endOfMonth(currentDate);

    const eventsMap = new Map<string, CalendarEvent[]>();

    // Add today's tasks to calendar
    tasks.forEach((task) => {
      const dateKey = format(new Date(), "yyyy-MM-dd");
      const event: CalendarEvent = {
        id: task.id,
        title: task.title,
        startTime: task.time || "09:00",
        endTime: task.time || "10:00",
        date: dateKey,
        type: task.type === "meeting" ? "meeting" : "task",
        completed: task.completed,
        source: "manual",
      };

      const dayEvents = eventsMap.get(dateKey) || [];
      dayEvents.push(event);
      eventsMap.set(dateKey, dayEvents);
    });

    // Add plan blocks to calendar
    if (plan) {
      plan.blocks.forEach((block) => {
        const dateKey = format(new Date(), "yyyy-MM-dd");
        const event: CalendarEvent = {
          id: block.id,
          title: block.title,
          startTime: block.startTime,
          endTime: block.endTime,
          date: dateKey,
          type: block.type === "focus" ? "focus" : "routine",
          source: "manual",
        };

        const dayEvents = eventsMap.get(dateKey) || [];
        dayEvents.push(event);
        eventsMap.set(dateKey, dayEvents);
      });
    }

    setCalendarEvents(eventsMap);
  };

  const handleToggleComplete = async (task: Task) => {
    try {
      await apiMethods.updateTask(task.id, { completed: !task.completed });
      // Force reload both tasks and calendar events
      await loadTodayData();
      await loadCalendarEvents();
    } catch (error) {
      console.error("Failed to update task:", error);
    }
  };

  const handleAddTask = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const today = format(new Date(), "yyyy-MM-dd");
      const taskData = {
        type: newTask.type,
        title: newTask.title,
        duration: newTask.duration ? parseInt(newTask.duration) : undefined,
        time: newTask.time || undefined,
        completed: false,
        date: newTask.date || today,
      };

      await apiMethods.addTask(taskData);

      // Force reload both tasks and calendar events
      await loadTodayData();
      await loadCalendarEvents();

      setNewTask({
        type: "todo",
        title: "",
        description: "",
        duration: "",
        time: "",
        date: today,
      });
      setIsTaskModalOpen(false);
    } catch (error) {
      console.error("Failed to add task:", error);
      alert("Failed to add task. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleImportICS = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    try {
      const text = await file.text();

      // Basic ICS parsing (in production, use a library like ical.js)
      const events = parseICS(text);

      // Add imported events to calendar
      const newEventsMap = new Map(calendarEvents);
      events.forEach((event) => {
        const dateKey = event.date;
        const dayEvents = newEventsMap.get(dateKey) || [];
        dayEvents.push(event);
        newEventsMap.set(dateKey, dayEvents);
      });

      setCalendarEvents(newEventsMap);
    } catch (error) {
      console.error("Failed to import ICS:", error);
      alert("Failed to import calendar file");
    } finally {
      setIsLoading(false);
    }
  };

  // Basic ICS parser (simplified)
  const parseICS = (text: string): CalendarEvent[] => {
    const events: CalendarEvent[] = [];
    const lines = text.split("\n");
    let currentEvent: any = {};
    let inEvent = false;

    lines.forEach((line) => {
      const trimmed = line.trim();

      if (trimmed === "BEGIN:VEVENT") {
        inEvent = true;
        currentEvent = {};
      } else if (trimmed === "END:VEVENT" && inEvent) {
        if (currentEvent.dtstart && currentEvent.summary) {
          events.push({
            id: `ics-${Date.now()}-${Math.random()}`,
            title: currentEvent.summary,
            description: currentEvent.description || "",
            startTime:
              currentEvent.dtstart.split("T")[1]?.substring(0, 5) || "09:00",
            endTime:
              currentEvent.dtend?.split("T")[1]?.substring(0, 5) || "10:00",
            date: currentEvent.dtstart.split("T")[0],
            type: "imported",
            source: "ics",
          });
        }
        inEvent = false;
      } else if (inEvent) {
        if (trimmed.startsWith("SUMMARY:")) {
          currentEvent.summary = trimmed.substring(8);
        } else if (trimmed.startsWith("DESCRIPTION:")) {
          currentEvent.description = trimmed.substring(12);
        } else if (trimmed.startsWith("DTSTART:")) {
          const value = trimmed.substring(8);
          currentEvent.dtstart = value.replace(/[:-]/g, "").substring(0, 15);
        } else if (trimmed.startsWith("DTEND:")) {
          const value = trimmed.substring(6);
          currentEvent.dtend = value.replace(/[:-]/g, "").substring(0, 15);
        }
      }
    });

    return events;
  };

  const getTaskIcon = (type: string) => {
    switch (type) {
      case "gym":
        return "💪";
      case "meeting":
        return "📅";
      case "focus":
        return "🎯";
      case "routine":
        return "🔄";
      case "imported":
        return "📥";
      default:
        return "✓";
    }
  };

  const getTaskColor = (type: string) => {
    switch (type) {
      case "gym":
        return "bg-green-100 text-green-800 border-green-300";
      case "meeting":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "focus":
        return "bg-purple-100 text-purple-800 border-purple-300";
      case "routine":
        return "bg-orange-100 text-orange-800 border-orange-300";
      case "imported":
        return "bg-pink-100 text-pink-800 border-pink-300";
      default:
        return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  const getBlockIcon = (type: string) => {
    switch (type) {
      case "focus":
        return <Zap className="h-4 w-4" />;
      case "break":
        return <Coffee className="h-4 w-4" />;
      case "routine":
        return <Clock className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const getDayEvents = (date: Date) => {
    const dateKey = format(date, "yyyy-MM-dd");
    return calendarEvents.get(dateKey) || [];
  };

  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(currentDate);
  const daysInMonth = eachDayOfInterval({ start: monthStart, end: monthEnd });

  // Get day of week for first day (0 = Sunday)
  const firstDayOfWeek = monthStart.getDay();

  // Create padding for days before month starts
  const paddingDays = Array(firstDayOfWeek).fill(null);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      <Header />
      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Today's Actions Section */}
        <Card className="shadow-xl">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-3xl font-bold">
                  Today's Actions 📋
                </CardTitle>
                <CardDescription className="text-lg mt-2">
                  {format(new Date(), "EEEE, MMMM d, yyyy")}
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Dialog
                  open={isTaskModalOpen}
                  onOpenChange={setIsTaskModalOpen}
                >
                  <DialogTrigger asChild>
                    <Button>
                      <Plus className="mr-2 h-4 w-4" />
                      Add Task
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-[500px]">
                    <form onSubmit={handleAddTask}>
                      <DialogHeader>
                        <DialogTitle>Create New Task</DialogTitle>
                        <DialogDescription>
                          Add a new task, meeting, or gym session
                        </DialogDescription>
                      </DialogHeader>
                      <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                          <Label htmlFor="task-type">Type</Label>
                          <Select
                            value={newTask.type}
                            onValueChange={(
                              value: "todo" | "gym" | "meeting"
                            ) => setNewTask({ ...newTask, type: value })}
                          >
                            <SelectTrigger id="task-type">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="todo">✓ To-Do</SelectItem>
                              <SelectItem value="gym">
                                💪 Gym Session
                              </SelectItem>
                              <SelectItem value="meeting">
                                📅 Meeting
                              </SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="grid gap-2">
                          <Label htmlFor="task-title">Title</Label>
                          <Input
                            id="task-title"
                            placeholder="What needs to be done?"
                            value={newTask.title}
                            onChange={(e) =>
                              setNewTask({ ...newTask, title: e.target.value })
                            }
                            required
                          />
                        </div>
                        <div className="grid gap-2">
                          <Label htmlFor="task-description">
                            Description (optional)
                          </Label>
                          <Textarea
                            id="task-description"
                            placeholder="Add more details..."
                            value={newTask.description}
                            onChange={(e) =>
                              setNewTask({
                                ...newTask,
                                description: e.target.value,
                              })
                            }
                            rows={3}
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="grid gap-2">
                            <Label htmlFor="task-duration">
                              Duration (min)
                            </Label>
                            <Input
                              id="task-duration"
                              type="number"
                              placeholder="30"
                              value={newTask.duration}
                              onChange={(e) =>
                                setNewTask({
                                  ...newTask,
                                  duration: e.target.value,
                                })
                              }
                            />
                          </div>
                          <div className="grid gap-2">
                            <Label htmlFor="task-time">Time</Label>
                            <Input
                              id="task-time"
                              type="time"
                              value={newTask.time}
                              onChange={(e) =>
                                setNewTask({ ...newTask, time: e.target.value })
                              }
                            />
                          </div>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button
                          type="submit"
                          disabled={isLoading || !newTask.title.trim()}
                        >
                          {isLoading ? "Adding..." : "Add Task"}
                        </Button>
                      </DialogFooter>
                    </form>
                  </DialogContent>
                </Dialog>

                <Button variant="outline" asChild>
                  <label className="cursor-pointer">
                    <Upload className="mr-2 h-4 w-4" />
                    Import .ics
                    <input
                      type="file"
                      accept=".ics,.ical"
                      className="hidden"
                      onChange={handleImportICS}
                    />
                  </label>
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {/* Tasks */}
            {tasks.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <span>📝</span> Tasks
                </h3>
                <div className="space-y-2">
                  {tasks.map((task) => (
                    <div
                      key={task.id}
                      className={`flex items-center gap-3 p-3 rounded-lg border ${
                        task.completed ? "bg-gray-50 opacity-60" : "bg-white"
                      } hover:shadow-md transition-all`}
                    >
                      <button
                        onClick={() => handleToggleComplete(task)}
                        className="flex-shrink-0"
                      >
                        {task.completed ? (
                          <CheckCircle2 className="h-5 w-5 text-green-500" />
                        ) : (
                          <Circle className="h-5 w-5 text-gray-300" />
                        )}
                      </button>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span>{getTaskIcon(task.type)}</span>
                          <h4
                            className={`font-semibold ${
                              task.completed ? "line-through text-gray-400" : ""
                            }`}
                          >
                            {task.title}
                          </h4>
                          <Badge
                            className={getTaskColor(task.type)}
                            variant="outline"
                          >
                            {task.type}
                          </Badge>
                        </div>
                        {(task.duration || task.time) && (
                          <div className="text-sm text-gray-500 mt-1">
                            {task.time && <span>{task.time}</span>}
                            {task.duration && task.time && <span> • </span>}
                            {task.duration && <span>{task.duration} min</span>}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Focus Blocks */}
            {plan && plan.blocks.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <span>🎯</span> Focus Blocks
                </h3>
                <div className="space-y-2">
                  {plan.blocks.map((block: FocusBlock) => (
                    <div
                      key={block.id}
                      className={`p-3 rounded-lg border bg-white hover:shadow-md transition-all ${
                        isToday(new Date())
                          ? "border-l-4 border-l-blue-500"
                          : ""
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {getBlockIcon(block.type)}
                          <div>
                            <h4 className="font-semibold">{block.title}</h4>
                            <div className="text-sm text-gray-500">
                              {block.startTime} - {block.endTime} (
                              {block.duration} min)
                            </div>
                          </div>
                          <Badge
                            className={getTaskColor(block.type)}
                            variant="outline"
                          >
                            {block.type}
                          </Badge>
                        </div>
                        {block.type === "focus" && (
                          <Button
                            size="sm"
                            onClick={() => navigate(`/focus/${block.id}`)}
                          >
                            <Play className="mr-2 h-4 w-4" />
                            Start
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Routines */}
            {plan &&
              (plan.morningRoutine?.length > 0 ||
                plan.eveningRoutine?.length > 0) && (
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <span>🔄</span> Routines
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {plan.morningRoutine && plan.morningRoutine.length > 0 && (
                      <div className="p-3 rounded-lg border bg-white">
                        <h4 className="font-semibold mb-2">☀️ Morning</h4>
                        <ul className="space-y-1 text-sm">
                          {plan.morningRoutine.map((item, idx) => (
                            <li key={idx} className="flex items-start gap-2">
                              <span className="text-blue-500">•</span>
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {plan.eveningRoutine && plan.eveningRoutine.length > 0 && (
                      <div className="p-3 rounded-lg border bg-white">
                        <h4 className="font-semibold mb-2">🌙 Evening</h4>
                        <ul className="space-y-1 text-sm">
                          {plan.eveningRoutine.map((item, idx) => (
                            <li key={idx} className="flex items-start gap-2">
                              <span className="text-indigo-500">•</span>
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

            {tasks.length === 0 && !plan && (
              <div className="text-center py-12 text-gray-500">
                <p className="text-lg mb-4">
                  No activities scheduled for today
                </p>
                <Button onClick={() => setIsTaskModalOpen(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Your First Task
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Calendar Section */}
        <Card className="shadow-xl">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-2xl font-bold">
                <CalendarIcon className="inline mr-2 h-6 w-6" />
                Calendar
              </CardTitle>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentDate(subMonths(currentDate, 1))}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-lg font-semibold min-w-[200px] text-center">
                  {format(currentDate, "MMMM yyyy")}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentDate(addMonths(currentDate, 1))}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-7 gap-2">
              {/* Day headers */}
              {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
                <div
                  key={day}
                  className="text-center text-sm font-semibold text-gray-600 py-2"
                >
                  {day}
                </div>
              ))}

              {/* Padding days */}
              {paddingDays.map((_, idx) => (
                <div key={`padding-${idx}`} className="aspect-square" />
              ))}

              {/* Calendar days */}
              {daysInMonth.map((day) => {
                const dayEvents = getDayEvents(day);
                const isCurrentDay = isToday(day);

                return (
                  <div
                    key={day.toString()}
                    className={`aspect-square border rounded-lg p-2 cursor-pointer transition-all hover:shadow-md ${
                      isCurrentDay
                        ? "bg-blue-100 border-blue-500 border-2"
                        : "bg-white hover:bg-gray-50"
                    }`}
                    onClick={() => {
                      setSelectedDate(day);
                      if (dayEvents.length > 0) {
                        setSelectedEvent(dayEvents[0]);
                        setIsEventModalOpen(true);
                      }
                    }}
                  >
                    <div
                      className={`text-sm font-semibold mb-1 ${
                        isCurrentDay ? "text-blue-700" : "text-gray-700"
                      }`}
                    >
                      {format(day, "d")}
                    </div>
                    {dayEvents.length > 0 && (
                      <div className="space-y-1">
                        {dayEvents.slice(0, 2).map((event) => (
                          <div
                            key={event.id}
                            className={`text-xs truncate px-1 py-0.5 rounded ${getTaskColor(
                              event.type
                            )}`}
                            title={event.title}
                          >
                            {event.title}
                          </div>
                        ))}
                        {dayEvents.length > 2 && (
                          <div className="text-xs text-gray-500 px-1">
                            +{dayEvents.length - 2} more
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Event Detail Modal */}
        <Dialog open={isEventModalOpen} onOpenChange={setIsEventModalOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {selectedDate && format(selectedDate, "MMMM d, yyyy")}
              </DialogTitle>
              <DialogDescription>Events for this day</DialogDescription>
            </DialogHeader>
            {selectedDate && (
              <ScrollArea className="max-h-[400px]">
                <div className="space-y-3">
                  {getDayEvents(selectedDate).map((event) => (
                    <div
                      key={event.id}
                      className={`p-3 rounded-lg border ${getTaskColor(
                        event.type
                      )}`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span>{getTaskIcon(event.type)}</span>
                            <h4 className="font-semibold">{event.title}</h4>
                          </div>
                          {event.description && (
                            <p className="text-sm mb-2">{event.description}</p>
                          )}
                          <div className="text-sm flex items-center gap-2">
                            <Clock className="h-3 w-3" />
                            {event.startTime} - {event.endTime}
                          </div>
                        </div>
                        {event.completed !== undefined && (
                          <div>
                            {event.completed ? (
                              <CheckCircle2 className="h-5 w-5 text-green-500" />
                            ) : (
                              <Circle className="h-5 w-5 text-gray-300" />
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {getDayEvents(selectedDate).length === 0 && (
                    <p className="text-center text-gray-500 py-4">
                      No events for this day
                    </p>
                  )}
                </div>
              </ScrollArea>
            )}
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsEventModalOpen(false)}
              >
                Close
              </Button>
              <Button
                onClick={() => {
                  setIsEventModalOpen(false);
                  setIsTaskModalOpen(true);
                }}
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Task
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
