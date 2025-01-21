// src/components/LoginForm.tsx
import React, { useState } from "react";
import { TextField, Button, Stack } from "@mui/material";
import { loginUser } from "../api/auth";

interface Props {
  onLoginSuccess: (username: string) => void;
}

export function LoginForm({ onLoginSuccess }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrorMsg("");

    try {
      const resp = await loginUser(username, password);
      if ("error" in resp) {
        setErrorMsg(resp.error);
      } else if (resp.result === "ok") {
        onLoginSuccess(username);
        localStorage.setItem("token", resp.token);
      }
    } catch (err) {
      setErrorMsg("Something went wrong. Check console.");
      console.error(err);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <Stack spacing={2} sx={{ width: 300, margin: "auto" }}>
        <TextField
          label="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <TextField
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <Button variant="contained" type="submit">
          Login
        </Button>
        {errorMsg && <p style={{ color: "red" }}>{errorMsg}</p>}
      </Stack>
    </form>
  );
}
