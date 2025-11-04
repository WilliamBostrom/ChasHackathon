import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "~/components/ui/card";
import { Button } from "~/components/ui/button";
import { Progress } from "~/components/ui/progress";
import { apiMethods } from "~/lib/api";
import {
  Play,
  Pause,
  SkipForward,
  ThumbsUp,
  ThumbsDown,
  Meh,
} from "lucide-react";

export default function FocusPage() {
  const { blockId } = useParams();
  const navigate = useNavigate();
  const [blockTitle, setBlockTitle] = useState("Focus Block");
  const [totalSeconds, setTotalSeconds] = useState(25 * 60); // 25 minutes default
  const [remainingSeconds, setRemainingSeconds] = useState(25 * 60);
  const [isRunning, setIsRunning] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState(false);

  useEffect(() => {
    if (blockId) {
      startBlock();
    }
  }, [blockId]);

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;

    if (isRunning && remainingSeconds > 0) {
      interval = setInterval(() => {
        setRemainingSeconds((prev) => {
          if (prev <= 1) {
            setIsRunning(false);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRunning, remainingSeconds]);

  const startBlock = async () => {
    try {
      if (blockId) {
        const response = await apiMethods.startFocusBlock(blockId);
        setBlockTitle(response.title || "Focus Block");
        setTotalSeconds(response.duration * 60 || 25 * 60);
        setRemainingSeconds(response.duration * 60 || 25 * 60);
        setIsRunning(true);
      }
    } catch (error) {
      console.error("Failed to start block:", error);
      // Use defaults if API fails
      setIsRunning(true);
    }
  };

  const handleToggleTimer = () => {
    setIsRunning(!isRunning);
  };

  const handleSkip = () => {
    navigate("/plan");
  };

  const handleFeedback = async (feedback: string) => {
    try {
      if (blockId) {
        await apiMethods.submitFocusFeedback(blockId, feedback);
        setFeedbackSent(true);
        setTimeout(() => {
          navigate("/plan");
        }, 1500);
      }
    } catch (error) {
      console.error("Failed to submit feedback:", error);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
  };

  const progress = ((totalSeconds - remainingSeconds) / totalSeconds) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100 flex items-center justify-center p-6">
      <Card className="w-full max-w-2xl shadow-2xl">
        <CardHeader className="text-center">
          <CardTitle className="text-4xl font-bold text-gray-800">
            {blockTitle}
          </CardTitle>
          <CardDescription className="text-lg mt-2">
            Stay focused and flow with your work
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-8">
          <div className="text-center space-y-4">
            <div className="text-8xl font-bold text-purple-600 font-mono">
              {formatTime(remainingSeconds)}
            </div>
            <Progress value={progress} className="h-3" />
          </div>

          {remainingSeconds > 0 ? (
            <div className="flex gap-4 justify-center">
              <Button
                onClick={handleToggleTimer}
                size="lg"
                className="px-8"
                variant={isRunning ? "outline" : "default"}
              >
                {isRunning ? (
                  <>
                    <Pause className="mr-2 h-5 w-5" />
                    Pause
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-5 w-5" />
                    Resume
                  </>
                )}
              </Button>
              <Button onClick={handleSkip} size="lg" variant="outline">
                <SkipForward className="mr-2 h-5 w-5" />
                Skip
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600 mb-4">
                  🎉 Great work!
                </p>
                <p className="text-lg text-gray-600 mb-6">
                  How did this focus session go?
                </p>
              </div>

              {!feedbackSent ? (
                <div className="grid grid-cols-3 gap-4">
                  <Button
                    onClick={() => handleFeedback("great")}
                    size="lg"
                    variant="outline"
                    className="flex flex-col h-24 hover:bg-green-50"
                  >
                    <ThumbsUp className="h-8 w-8 mb-2 text-green-600" />
                    <span>Great!</span>
                  </Button>
                  <Button
                    onClick={() => handleFeedback("okay")}
                    size="lg"
                    variant="outline"
                    className="flex flex-col h-24 hover:bg-yellow-50"
                  >
                    <Meh className="h-8 w-8 mb-2 text-yellow-600" />
                    <span>Okay</span>
                  </Button>
                  <Button
                    onClick={() => handleFeedback("difficult")}
                    size="lg"
                    variant="outline"
                    className="flex flex-col h-24 hover:bg-red-50"
                  >
                    <ThumbsDown className="h-8 w-8 mb-2 text-red-600" />
                    <span>Difficult</span>
                  </Button>
                </div>
              ) : (
                <div className="text-center">
                  <p className="text-lg text-green-600 font-semibold">
                    ✓ Feedback recorded! Returning to plan...
                  </p>
                </div>
              )}
            </div>
          )}

          <div className="text-center text-sm text-gray-500">
            <p>💡 Tip: Take breaks regularly to maintain mental clarity</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
