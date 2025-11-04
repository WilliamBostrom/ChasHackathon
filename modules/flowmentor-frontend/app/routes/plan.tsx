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
import { apiMethods, type DayPlan, type FocusBlock } from "~/lib/api";
import { Clock, Play, Coffee, Zap } from "lucide-react";

export default function PlanPage() {
  const navigate = useNavigate();
  const [plan, setPlan] = useState<DayPlan | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadPlan();
  }, []);

  const loadPlan = async () => {
    try {
      const today = new Date().toISOString().split("T")[0];
      const data = await apiMethods.getDayPlan(today);
      setPlan(data);
    } catch (error) {
      console.error("Failed to load plan:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartFocus = (blockId: string) => {
    navigate(`/focus/${blockId}`);
  };

  const getBlockIcon = (type: string) => {
    switch (type) {
      case "focus":
        return <Zap className="h-5 w-5" />;
      case "break":
        return <Coffee className="h-5 w-5" />;
      case "routine":
        return <Clock className="h-5 w-5" />;
      default:
        return <Clock className="h-5 w-5" />;
    }
  };

  const getBlockColor = (type: string) => {
    switch (type) {
      case "focus":
        return "bg-blue-100 border-blue-300 text-blue-800";
      case "break":
        return "bg-green-100 border-green-300 text-green-800";
      case "routine":
        return "bg-purple-100 border-purple-300 text-purple-800";
      default:
        return "bg-gray-100 border-gray-300 text-gray-800";
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <Header />
        <div className="flex items-center justify-center min-h-[calc(100vh-80px)]">
          <Card className="w-96 shadow-xl">
            <CardContent className="pt-6">
              <div className="text-center space-y-4">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-lg font-semibold">Loading your AI plan...</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <Header />
        <div className="flex items-center justify-center p-6 min-h-[calc(100vh-80px)]">
          <Card className="w-full max-w-md shadow-xl">
            <CardContent className="pt-6">
              <div className="text-center space-y-4">
                <p className="text-lg">No plan found for today</p>
                <Button onClick={() => navigate("/tasks")}>
                  Back to Tasks
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header />
      <div className="p-6">
        <div className="max-w-5xl mx-auto space-y-6">
          <Card className="shadow-xl">
            <CardHeader>
              <CardTitle className="text-3xl font-bold">
                Your AI-Generated Day Plan 🎯
              </CardTitle>
              <CardDescription className="text-lg">
                Optimized for maximum productivity and well-being
              </CardDescription>
            </CardHeader>
          </Card>

          {plan.morningRoutine && plan.morningRoutine.length > 0 && (
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="text-xl flex items-center gap-2">
                  <span>☀️</span> Morning Routine
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {plan.morningRoutine.map((item, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-blue-600 font-bold">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="text-xl">Focus Blocks</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {plan.blocks.map((block: FocusBlock) => (
                  <div
                    key={block.id}
                    className={`p-4 rounded-lg border-2 ${getBlockColor(
                      block.type
                    )}`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3 flex-1">
                        <div className="mt-1">{getBlockIcon(block.type)}</div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="font-bold text-lg">{block.title}</h3>
                            <Badge variant="outline" className="capitalize">
                              {block.type}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-4 text-sm">
                            <span className="flex items-center gap-1">
                              <Clock className="h-4 w-4" />
                              {block.startTime} - {block.endTime}
                            </span>
                            <span>{block.duration} min</span>
                          </div>
                        </div>
                      </div>
                      {block.type === "focus" && (
                        <Button
                          onClick={() => handleStartFocus(block.id)}
                          size="sm"
                          className="flex-shrink-0"
                        >
                          <Play className="mr-2 h-4 w-4" />
                          Start
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {plan.eveningRoutine && plan.eveningRoutine.length > 0 && (
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="text-xl flex items-center gap-2">
                  <span>🌙</span> Evening Routine
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {plan.eveningRoutine.map((item, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-indigo-600 font-bold">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          <div className="flex gap-4">
            <Button
              onClick={() => navigate("/tasks")}
              variant="outline"
              className="flex-1"
            >
              Edit Tasks
            </Button>
            <Button onClick={() => navigate("/afternoon")} className="flex-1">
              Continue to Afternoon
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
