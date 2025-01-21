// src/App.tsx
import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { GameTable } from "./components/GameTable";
import { LoginForm } from "./components/LoginForm";
import { LobbyDetail } from "./containers/LobbyDetail";
import { LobbyList } from "./containers/LobbyList";
import { apiClient } from "./api";

function App() {
  const [user, setUser] = useState<string | null>(null);

  useEffect(function checkForToken() {
    const token = localStorage.getItem("token");
    if (token) {
      apiClient("/users/me")
        .then((resp) => resp.json())
        .then((resp) => setUser(resp.user))
        .catch((err) => {
          console.log(err);
          localStorage.removeItem("token");
        });
    }
  }, []);

  return (
    <BrowserRouter>
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
              <LoginForm onLoginSuccess={(username) => setUser(username)} />
            )
          }
        />

        {/* Lobbies list route: if not logged in, redirect to "/", otherwise show LobbyList */}
        <Route
          path="/lobbies"
          element={
            user ? <LobbyList username={user} /> : <Navigate to="/" replace />
          }
        />

        {/* Lobby detail route */}
        <Route
          path="/lobbies/:lobbyId"
          element={
            user ? <LobbyDetail username={user} /> : <Navigate to="/" replace />
          }
        />

        {/* Game table route */}
        <Route
          path="/game/:lobbyId/:username"
          element={user ? <GameTable /> : <Navigate to="/" replace />}
        />

        {/* Catch-all for any unknown paths */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
