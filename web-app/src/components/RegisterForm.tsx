import { Box, Button, Link, Stack, TextField, Typography } from "@mui/material";
import React, { useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { registerUser } from "../api/auth";

interface Props {
  onRegisterSuccess: (username: string) => void;
}

export function RegisterForm({ onRegisterSuccess }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrorMsg("");

    try {
      const resp = await registerUser(username, password);
      if ("error" in resp) {
        setErrorMsg(resp.error);
      } else if (resp.result === "ok") {
        onRegisterSuccess(username);
        localStorage.setItem("token", resp.token);
        navigate("/");
      }
    } catch (err) {
      setErrorMsg("Something went wrong. Check console.");
      console.error(err);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <Stack spacing={2} sx={{ width: 300, margin: "auto" }}>
        <Stack direction="row" justifyContent="center">
          <Box
            component="img"
            src="/logo.png"
            sx={{ width: 150, margin: "auto" }}
          />
        </Stack>
        <Typography variant="h2">Register new user</Typography>
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
          Register
        </Button>
        {errorMsg && <p style={{ color: "red" }}>{errorMsg}</p>}
        <Stack direction="row" justifyContent="space-between">
          <Typography variant="subtitle1">Already have an account?</Typography>
          <Link
            component={RouterLink}
            to={"/?" + new URLSearchParams(window.location.search).toString()}
          >
            Log in instead
          </Link>
        </Stack>
      </Stack>
    </form>
  );
}
