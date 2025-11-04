import { useState } from "react";
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
import { Textarea } from "~/components/ui/textarea";
import { Label } from "~/components/ui/label";
import { apiMethods } from "~/lib/api";
import { Sparkles } from "lucide-react";

export default function AfternoonReflection() {
  const navigate = useNavigate();
  const [accomplishments, setAccomplishments] = useState("");
  const [challenges, setChallenges] = useState("");
  const [learnings, setLearnings] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [aiSummary, setAiSummary] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await apiMethods.submitAfternoonReflection({
        accomplishments,
        challenges,
        learnings,
        date: new Date().toISOString().split("T")[0],
      });

      // Get AI summary
      const today = new Date().toISOString().split("T")[0];
      const summary = await apiMethods.getAISummary(today);
      setAiSummary(
        summary.summary || "Great work today! Keep building momentum."
      );
      setShowSummary(true);
    } catch (error) {
      console.error("Failed to submit reflection:", error);
      setAiSummary("Great work today! Keep building momentum.");
      setShowSummary(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleContinue = () => {
    navigate("/weekly");
  };

  if (showSummary) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 to-yellow-100">
        <Header />
        <div className="flex items-center justify-center p-6">
          <Card className="w-full max-w-2xl shadow-xl">
            <CardHeader className="text-center">
              <div className="flex justify-center mb-4">
                <Sparkles className="h-16 w-16 text-yellow-500" />
              </div>
              <CardTitle className="text-3xl font-bold text-gray-800">
                AI Day Summary
              </CardTitle>
              <CardDescription className="text-lg mt-2">
                Here's what you accomplished today
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="bg-gradient-to-r from-yellow-50 to-orange-50 p-6 rounded-lg border-2 border-yellow-200">
                <p className="text-lg leading-relaxed text-gray-700 whitespace-pre-wrap">
                  {aiSummary}
                </p>
              </div>

              <div className="space-y-4">
                <p className="text-center text-gray-600 text-lg">
                  Ready to plan for tomorrow?
                </p>
                <div className="flex gap-4">
                  <Button
                    onClick={() => navigate("/morning")}
                    variant="outline"
                    className="flex-1"
                  >
                    Tomorrow Morning
                  </Button>
                  <Button onClick={handleContinue} className="flex-1">
                    View Weekly Summary
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-yellow-100">
      <Header />
      <div className="flex items-center justify-center p-6">
        <Card className="w-full max-w-2xl shadow-xl">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold text-gray-800">
              Afternoon Reflection 🌅
            </CardTitle>
            <CardDescription className="text-lg mt-2">
              Take a moment to reflect on your day
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label
                  htmlFor="accomplishments"
                  className="text-lg font-semibold"
                >
                  What did you accomplish today?
                </Label>
                <Textarea
                  id="accomplishments"
                  placeholder="I completed the project proposal, had a productive meeting with the team..."
                  value={accomplishments}
                  onChange={(e) => setAccomplishments(e.target.value)}
                  className="min-h-[120px] resize-none"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="challenges" className="text-lg font-semibold">
                  What challenges did you face?
                </Label>
                <Textarea
                  id="challenges"
                  placeholder="I struggled with time management during the afternoon..."
                  value={challenges}
                  onChange={(e) => setChallenges(e.target.value)}
                  className="min-h-[120px] resize-none"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="learnings" className="text-lg font-semibold">
                  What did you learn?
                </Label>
                <Textarea
                  id="learnings"
                  placeholder="I learned that taking breaks actually improves my focus..."
                  value={learnings}
                  onChange={(e) => setLearnings(e.target.value)}
                  className="min-h-[120px] resize-none"
                  required
                />
              </div>

              <Button
                type="submit"
                className="w-full text-lg py-6"
                disabled={
                  isSubmitting ||
                  !accomplishments.trim() ||
                  !challenges.trim() ||
                  !learnings.trim()
                }
              >
                {isSubmitting ? "Generating Summary..." : "Get AI Summary ✨"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
