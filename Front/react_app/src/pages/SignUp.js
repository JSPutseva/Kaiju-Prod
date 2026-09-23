import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useTheme } from "../context/ThemeContext";

export default function SignUp() {
  const navigate = useNavigate();
  const { theme } = useTheme();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!name || !email || !password || !confirmPassword) {
      setError("Fill in all fields.");
      return;
    }

    if (name.length > 100) {
      setError("Name must be 100 characters or fewer.");
      return;
    }

    if (!/^\S+@\S+\.\S+$/.test(email)) {
      setError("Enter a valid email address.");
      return;
    }

    if (password.length < 8 || password.length > 128) {
      setError("Password must be between 8 and 128 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }

    setError(null);
    setLoading(true);

    try {
      await api.register({
        name,
        email,
        password,
      });

      navigate("/login");
    } catch (err) {
      setError(err.message || "Unable to create the account.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 dark:bg-gray-900">
      <div className="w-full max-w-sm rounded-lg border border-[#FBD98A] bg-white p-8 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="mb-6 flex flex-col items-center gap-2">
          <img
            src={theme === "dark" ? "/logo_dark.png" : "/logo.png"}
            alt="Kaiju logo"
            className="h-12 w-12 object-contain"
          />

          <h1 className="font-display text-3xl text-gray-900 dark:text-gray-100">
            Kaiju
          </h1>

          <p className="text-sm text-gray-500 dark:text-gray-400">
            Create your officer account
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Name

            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Jane Tanaka"
              maxLength={100}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:border-[#F47E00] dark:focus:border-[#F8A201] focus:outline-none dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
            />
            <span className="mt-1 block text-xs font-normal text-gray-400 dark:text-gray-500">Up to 100 characters.</span>
          </label>

          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Email

            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@tokyork.gov"
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:border-[#F47E00] dark:focus:border-[#F8A201] focus:outline-none dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
            />
            <span className="mt-1 block text-xs font-normal text-gray-400 dark:text-gray-500">A valid email address.</span>
          </label>

          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Password

            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              minLength={8}
              maxLength={128}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:border-[#F47E00] dark:focus:border-[#F8A201] focus:outline-none dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
            />
            <span className="mt-1 block text-xs font-normal text-gray-400 dark:text-gray-500">8 to 128 characters.</span>
          </label>

          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Confirm password

            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:border-[#F47E00] dark:focus:border-[#F8A201] focus:outline-none dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
            />
            <span className="mt-1 block text-xs font-normal text-gray-400 dark:text-gray-500">Must match the password above.</span>
          </label>

          <p className="text-sm text-gray-500 dark:text-gray-400">
            A City Director will assign your role (QC, LC, or CD) after your account is created.
          </p>

          {error && (
            <p className="text-sm text-[#dc2626] dark:text-red-400">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-[#F47E00] dark:bg-[#F8A201] py-2.5 text-base font-bold text-white hover:bg-[#D98C00] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-medium text-[#B36B00] hover:underline dark:text-[#FFC966]"
          >
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
