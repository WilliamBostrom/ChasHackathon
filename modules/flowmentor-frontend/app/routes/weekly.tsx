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
import { Progress } from "~/components/ui/progress";
import { apiMethods, type WeeklySummary, type MicroGoal } from "~/lib/api";
import { Target, TrendingUp, CheckCircle2 } from "lucide-react";

export default function WeeklySummaryPage() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<WeeklySummary | null>(null);
  const [selectedGoal, setSelectedGoal] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadWeeklySummary();
  }, []);

  const loadWeeklySummary = async () => {
    try {
      const currentWeek = getWeekNumber(new Date());
      const data = await apiMethods.getWeeklySummary(currentWeek);
      setSummary(data);
    } catch (error) {
      console.error("Failed to load weekly summary:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const getWeekNumber = (date: Date) => {
    const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
    const pastDaysOfYear =
      (date.getTime() - firstDayOfYear.getTime()) / 86400000;
    return Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
  };

  const handleSelectGoal = async (goalId: string) => {
    setIsSubmitting(true);
    try {
      await apiMethods.selectMicroGoal(goalId);
      setSelectedGoal(goalId);
      setTimeout(() => {
        navigate("/morning");
      }, 2000);
    } catch (error) {
      console.error("Failed to select goal:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-teal-100">
        <Header />
        <div className="flex items-center justify-center min-h-[calc(100vh-80px)]">
          <Card className="w-96 shadow-xl">
            <CardContent className="pt-6">
              <div className="text-center space-y-4">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto"></div>
                <p className="text-lg font-semibold">
                  Loading weekly insights...
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-teal-100">
        <Header />
        <div className="flex items-center justify-center p-6 min-h-[calc(100vh-80px)]">
          <Card className="w-full max-w-md shadow-xl">
            <CardContent className="pt-6">
              <div className="text-center space-y-4">
                <p className="text-lg">No weekly summary available yet</p>
                <Button onClick={() => navigate("/morning")}>
                  Start Your Week
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-teal-100">
      <Header />
      <div className="p-6">
        <div className="max-w-5xl mx-auto space-y-6">
          <Card className="shadow-xl">
            <CardHeader className="text-center">
              <div className="flex justify-center mb-4">
                <TrendingUp className="h-16 w-16 text-green-600" />
              </div>
              <CardTitle className="text-3xl font-bold text-gray-800">
                Your Weekly Summary 📊
              </CardTitle>
              <CardDescription className="text-lg mt-2">
                Week {summary.weekNumber} Performance & Insights
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="text-2xl">Completion Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-4xl font-bold text-green-600">
                    {summary.completionRate}%
                  </span>
                  <Badge
                    variant={
                      summary.completionRate >= 80 ? "default" : "outline"
                    }
                    className="text-lg px-4 py-2"
                  >
                    {summary.completionRate >= 80
                      ? "Excellent! 🎉"
                      : summary.completionRate >= 60
                        ? "Good Progress 👍"
                        : "Keep Going 💪"}
                  </Badge>
                </div>
                <Progress value={summary.completionRate} className="h-4" />
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="text-2xl">AI Insights</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-gradient-to-r from-teal-50 to-green-50 p-6 rounded-lg border-2 border-teal-200">
                <p className="text-lg leading-relaxed text-gray-700 whitespace-pre-wrap">
                  {summary.insights}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Target className="h-6 w-6" />
                AI-Suggested Micro-Goals
              </CardTitle>
              <CardDescription>
                Pick one goal to focus on this week
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                {summary.suggestedGoals.map((goal: MicroGoal) => (
                  <div
                    key={goal.id}
                    className={`p-6 rounded-lg border-2 transition-all ${
                      selectedGoal === goal.id
                        ? "border-green-500 bg-green-50"
                        : "border-gray-200 bg-white hover:border-green-300 hover:shadow-md"
                    }`}
                  >
                    <div className="space-y-3">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <h3 className="text-xl font-bold text-gray-800 mb-2">
                            {goal.title}
                          </h3>
                          <p className="text-gray-600 mb-3">
                            {goal.description}
                          </p>
                          <div className="bg-blue-50 p-4 rounded-md border border-blue-200">
                            <p className="text-sm font-semibold text-blue-800 mb-1">
                              🤖 AI Reasoning:
                            </p>
                            <p className="text-sm text-blue-700">
                              {goal.aiReasoning}
                            </p>
                          </div>
                        </div>
                      </div>
                      <Button
                        onClick={() => handleSelectGoal(goal.id)}
                        disabled={isSubmitting || selectedGoal !== null}
                        className="w-full"
                        variant={
                          selectedGoal === goal.id ? "default" : "outline"
                        }
                      >
                        {selectedGoal === goal.id ? (
                          <>
                            <CheckCircle2 className="mr-2 h-5 w-5" />
                            Selected! Starting...
                          </>
                        ) : (
                          "Choose This Goal"
                        )}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {!selectedGoal && (
            <Button
              onClick={() => navigate("/morning")}
              variant="outline"
              className="w-full"
            >
              Skip for Now
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
