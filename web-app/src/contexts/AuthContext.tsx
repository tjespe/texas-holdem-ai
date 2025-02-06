import { createContext, useContext } from "react";

interface AuthContext {
  username: string | null;
  logOut: () => void;
  logIn: (username: string) => void;
}
const AuthContext = createContext<AuthContext | null>(null);

export const AuthContextProvider = AuthContext.Provider;

export const useAuthContext = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error(
      "useAuthContext must be used within an AuthContextProvider"
    );
  }
  return context;
};
