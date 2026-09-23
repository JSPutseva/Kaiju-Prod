import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useCurrentUser } from "../context/CurrentUserContext";
import { useTheme } from "../context/ThemeContext";

export default function Login() {
  const navigate = useNavigate();
  const { login } = useCurrentUser();
  const { theme } = useTheme();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!email || !password) {
      setError("Enter your email and password.");
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const response = await api.login({ email, password });
      login(response.access_token, response.user);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Invalid email or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f9fafb] px-4 dark:bg-gray-900">
      <div className="w-full max-w-sm rounded-lg border border-[#FBD98A] bg-white p-8 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="mb-6 flex flex-col items-center gap-2">
          <img
            src={theme === "dark" ? "/logo_dark.png" : "/logo.png"}
            alt="Kaiju logo"
            className="h-12 w-12 object-contain"
          />
          <h1 className="font-display text-3xl text-gray-900 dark:text-gray-100">Kaiju</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Log in to the crisis manager</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@tokyork.gov"
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:border-[#F47E00] dark:focus:border-[#F8A201] focus:outline-none dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
            />
          </label>

          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:border-[#F47E00] dark:focus:border-[#F8A201] focus:outline-none dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
            />
          </label>

          {error && <p className="text-sm text-[#dc2626] dark:text-red-400">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-[#F47E00] dark:bg-[#F8A201] py-2.5 text-base font-bold text-white hover:bg-[#D98C00] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Logging in..." : "Log in"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
          No account yet?{" "}
          <Link to="/signup" className="font-medium text-[#B36B00] hover:underline dark:text-[#FFC966]">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
