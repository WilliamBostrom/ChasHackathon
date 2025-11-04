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

export default function MorningCheckIn() {
  const navigate = useNavigate();
  const [feeling, setFeeling] = useState("");
  const [focus, setFocus] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await apiMethods.submitMorningCheckIn({
        feeling,
        focus,
        date: new Date().toISOString().split("T")[0],
      });
      navigate("/tasks");
    } catch (error) {
      console.error("Failed to submit morning check-in:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header />
      <div className="flex items-center justify-center p-4">
        <Card className="w-full max-w-2xl shadow-xl">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold text-gray-800">
              Good Morning! ☀️
            </CardTitle>
            <CardDescription className="text-lg mt-2">
              Let's start your day with intention
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="feeling" className="text-lg font-semibold">
                  How do you feel today?
                </Label>
                <Textarea
                  id="feeling"
                  placeholder="I feel energized and ready to tackle my goals..."
                  value={feeling}
                  onChange={(e) => setFeeling(e.target.value)}
                  className="min-h-[120px] resize-none"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="focus" className="text-lg font-semibold">
                  What will you focus on today?
                </Label>
                <Textarea
                  id="focus"
                  placeholder="Today I will focus on completing the presentation and exercising..."
                  value={focus}
                  onChange={(e) => setFocus(e.target.value)}
                  className="min-h-[120px] resize-none"
                  required
                />
              </div>

              <Button
                type="submit"
                className="w-full text-lg py-6"
                disabled={isSubmitting || !feeling.trim() || !focus.trim()}
              >
                {isSubmitting ? "Starting Your Day..." : "Let's Begin! 🚀"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
