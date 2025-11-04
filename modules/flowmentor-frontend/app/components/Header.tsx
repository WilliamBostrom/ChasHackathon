import { Link, useLocation } from "react-router";
import {
  Home,
  Sunrise,
  ListTodo,
  Calendar,
  Target,
  Moon,
  TrendingUp,
  LayoutDashboard,
} from "lucide-react";

export default function Header() {
  const location = useLocation();

  const navItems = [
    { path: "/", label: "Home", icon: <Home className="h-4 w-4" /> },
    {
      path: "/dashboard",
      label: "Dashboard",
      icon: <LayoutDashboard className="h-4 w-4" />,
    },
    {
      path: "/morning",
      label: "Morning",
      icon: <Sunrise className="h-4 w-4" />,
    },
    { path: "/tasks", label: "Tasks", icon: <ListTodo className="h-4 w-4" /> },
    { path: "/plan", label: "Plan", icon: <Calendar className="h-4 w-4" /> },
    {
      path: "/afternoon",
      label: "Afternoon",
      icon: <Moon className="h-4 w-4" />,
    },
    {
      path: "/weekly",
      label: "Weekly",
      icon: <TrendingUp className="h-4 w-4" />,
    },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white/80 backdrop-blur-sm">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link
            to="/"
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          >
            <Target className="h-8 w-8 text-blue-500" />
            <span className="text-2xl font-bold text-gray-800">FlowMentor</span>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
                  location.pathname === item.path
                    ? "bg-blue-100 text-blue-700 font-semibold"
                    : "text-gray-700 hover:bg-gray-100"
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>

          <div className="md:hidden">
            <button className="px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Menu
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
