import { useNavigate } from "react-router";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "~/components/ui/card";
import { Button } from "~/components/ui/button";
import { Sunrise, Target, Brain, TrendingUp } from "lucide-react";

export default function Home() {
  const navigate = useNavigate();

  const features = [
    {
      icon: <Sunrise className="h-12 w-12 text-blue-500" />,
      title: "Morning Check-In",
      description: "Start your day with intention and clarity",
    },
    {
      icon: <Target className="h-12 w-12 text-purple-500" />,
      title: "Smart Task Planning",
      description: "Add tasks, gym sessions, and meetings effortlessly",
    },
    {
      icon: <Brain className="h-12 w-12 text-green-500" />,
      title: "AI Day Planning",
      description: "Get personalized focus blocks optimized by AI",
    },
    {
      icon: <TrendingUp className="h-12 w-12 text-orange-500" />,
      title: "Weekly Insights",
      description: "Track progress and get micro-goals for growth",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      <div className="container mx-auto px-6 py-12">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-gray-800 mb-4">
            FlowMentor 🌊
          </h1>
          <p className="text-2xl text-gray-600 mb-8">
            Your AI-powered productivity companion
          </p>
          <Button
            onClick={() => navigate("/morning")}
            size="lg"
            className="text-xl px-8 py-6"
          >
            Start Your Day ☀️
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {features.map((feature, index) => (
            <Card
              key={index}
              className="hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
            >
              <CardHeader className="text-center">
                <div className="flex justify-center mb-4">{feature.icon}</div>
                <CardTitle className="text-xl">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-center text-base">
                  {feature.description}
                </CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card className="max-w-3xl mx-auto shadow-xl">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl">How It Works</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold">
                  1
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-1">
                    Morning Check-In
                  </h3>
                  <p className="text-gray-600">
                    Share how you feel and what you'll focus on today
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-500 text-white flex items-center justify-center font-bold">
                  2
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-1">Add Your Tasks</h3>
                  <p className="text-gray-600">
                    Input to-dos, gym sessions, and meetings for the day
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center font-bold">
                  3
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-1">
                    Get Your AI Plan
                  </h3>
                  <p className="text-gray-600">
                    Receive optimized focus blocks and routines for maximum
                    productivity
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-orange-500 text-white flex items-center justify-center font-bold">
                  4
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-1">
                    Focus & Reflect
                  </h3>
                  <p className="text-gray-600">
                    Use the focus timer and reflect on your day's achievements
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-pink-500 text-white flex items-center justify-center font-bold">
                  5
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-1">Weekly Growth</h3>
                  <p className="text-gray-600">
                    Review insights and select AI-suggested micro-goals for
                    continuous improvement
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-8 text-center">
              <Button
                onClick={() => navigate("/morning")}
                size="lg"
                className="px-8"
              >
                Get Started Now 🚀
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
