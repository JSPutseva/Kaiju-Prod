import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "./context/ThemeContext";
import { DisasterLevelProvider } from "./context/DisasterLevelContext";
import { CurrentUserProvider, useCurrentUser } from "./context/CurrentUserContext";
import { WebSocketProvider } from "./context/WebSocketContext";
import { QuartersProvider } from "./context/QuartersContext";
import Dashboard from "./pages/Dashboard";
import KaijuPovPage from "./pages/KaijuPovPage";
import Login from "./pages/Login";
import SignUp from "./pages/SignUp";
import DisasterFrame from "./components/DisasterFrame";

function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useCurrentUser();

  if (loading) {
    return null;
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function App() {
  return (
    <ThemeProvider>
      <DisasterLevelProvider>
        <CurrentUserProvider>
          <WebSocketProvider>
            <QuartersProvider>
              <BrowserRouter>
                <DisasterFrame />
                <Routes>
                  <Route path="/login" element={<Login />} />
                  <Route path="/signup" element={<SignUp />} />
                  <Route
                    path="/dashboard"
                    element={
                      <RequireAuth>
                        <Dashboard />
                      </RequireAuth>
                    }
                  />
                  <Route
                    path="/kaiju-pov"
                    element={
                      <RequireAuth>
                        <KaijuPovPage />
                      </RequireAuth>
                    }
                  />
                  <Route path="*" element={<Navigate to="/login" replace />} />
                </Routes>
              </BrowserRouter>
            </QuartersProvider>
          </WebSocketProvider>
        </CurrentUserProvider>
      </DisasterLevelProvider>
    </ThemeProvider>
  );
}

export default App;
