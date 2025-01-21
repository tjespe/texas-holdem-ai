// src/api/auth.ts
import { apiClient } from ".";
import { loginResponseSchema, LoginResponse } from "../schemas/login";

export async function loginUser(
  username: string,
  password: string
): Promise<LoginResponse> {
  const resp = await apiClient("/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await resp.json();

  // Validate against Zod
  const parsed = loginResponseSchema.parse(data);
  return parsed;
}
