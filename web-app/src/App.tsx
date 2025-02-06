// src/App.tsx
import { Box, Link, Stack, Typography } from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import { Navigate, Route, Routes, Link as RouterLink } from "react-router-dom";
import { apiClient } from "./api";
import { LoginForm } from "./components/LoginForm";
import { RegisterForm } from "./components/RegisterForm";
import { ApplicationPage } from "./containers/ApplicationPage";
import { LobbyDetail } from "./containers/ApplicationPage/LobbyDetail";
import { LobbyList } from "./containers/ApplicationPage/LobbyList";
import { AuthContextProvider } from "./contexts/AuthContext";

function App() {
  const [user, setUser] = useState<string | null>(null);
  const [loadingUser, setLoadingUser] = useState(true);

  const logOut = useCallback(() => {
    localStorage.removeItem("token");
    setUser(null);
  }, []);

  useEffect(function checkForToken() {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoadingUser(false);
      return;
    }
    apiClient("/users/me")
      .then((resp) => resp.json())
      .then((resp) => setUser(resp.user))
      .catch((err) => {
        console.log(err);
        localStorage.removeItem("token");
      })
      .finally(() => setLoadingUser(false));
  }, []);

  if (loadingUser) {
    return (
      <Box
        justifyContent="center"
        alignItems="center"
        width="100vh"
        height="100vh"
        alignContent="center"
      >
        <Typography variant="body1" textAlign="center">
          Loading...
        </Typography>
      </Box>
    );
  }

  const loginRedirectElement = (
    <Navigate
      to={"/?return=" + encodeURIComponent(window.location.pathname)}
      replace
    />
  );

  const handleLoginSuccess = (username: string) => {
    setUser(username);
    const searchParams = new URLSearchParams(window.location.search);
    console.log(searchParams);

    const returnPath = searchParams.get("return");
    if (returnPath) {
      const decoded = decodeURIComponent(returnPath);
      console.log("Redirecting to", decoded);

      window.location.href = decoded;
    } else {
      console.log("No return path, redirecting to /");
    }
  };

  return (
    <AuthContextProvider value={{ username: user, logIn: setUser, logOut }}>
      <Routes>
        {/* 
          1) If user is not logged in, show <LoginForm>, else go to "/lobbies".
          2) For clarity, we use path="/" for the login screen. 
        */}
        <Route
          path="/"
          element={
            user ? (
              <Navigate to="/lobbies" replace />
            ) : (
              <LoginForm onLoginSuccess={handleLoginSuccess} />
            )
          }
        />

        <Route
          path="/register"
          element={<RegisterForm onRegisterSuccess={handleLoginSuccess} />}
        />

        <Route element={<ApplicationPage />}>
          <Route
            path="/lobbies"
            element={user ? <LobbyList /> : loginRedirectElement}
          />
          <Route
            path="/lobbies/:lobbyId"
            element={user ? <LobbyDetail /> : loginRedirectElement}
          />
        </Route>

        {/* Catch-all for any unknown paths */}
        <Route
          path="*"
          element={
            <Box
              justifyContent="center"
              alignItems="center"
              width="100vh"
              height="100vh"
              alignContent="center"
            >
              <Stack
                width="fit-content"
                spacing={2}
                margin="auto"
                justifyContent="center"
                alignItems="center"
              >
                <Typography variant="h3" textAlign="center">
                  Nothing here!
                </Typography>
                <Link component={RouterLink} to="/">
                  Go to main page
                </Link>
              </Stack>
            </Box>
          }
        />
      </Routes>
    </AuthContextProvider>
  );
}

export default App;
