// src/theme.ts
import { createTheme } from "@mui/material/styles";

export const darkTheme = createTheme({
  palette: {
    mode: "dark", // Set to dark mode for a casino feel
    primary: {
      main: "#228B22", // Green felt table color
    },
    secondary: {
      main: "#D72638", // Red (inspired by hearts/diamonds)
    },
    background: {
      default: "#1C1C1C", // Dark casino background
      paper: "#2B2B2B", // Slightly lighter for cards/buttons
    },
    text: {
      primary: "#FFFFFF", // White text
      secondary: "#C0C0C0", // Subtle grey
    },
    error: {
      main: "#FF4C4C", // Bright red for mistakes
    },
    success: {
      main: "#2ECC71", // Poker chip green for correct actions
    },
    warning: {
      main: "#FFA500", // Orange for caution
    },
    info: {
      main: "#4DA8DA", // Cool blue for information
    },
  },
  typography: {
    fontFamily: `"Play", "Roboto", "Arial", sans-serif`,
    h1: {
      fontFamily: `"Cinzel", "Play", "Roboto", sans-serif`, // Fancy title font
      fontWeight: 700,
      fontSize: "2.5rem",
      color: "#FFD700", // Gold color for key elements
    },
    h2: {
      fontFamily: `"Cinzel", "Roboto", sans-serif`,
      fontWeight: 600,
      fontSize: "2rem",
      color: "#FFFFFF",
    },
    h3: {
      fontWeight: 500,
      fontSize: "1.75rem",
      color: "#C0C0C0",
    },
    body1: {
      fontSize: "1rem",
      fontWeight: 400,
    },
    button: {
      textTransform: "none", // More elegant look for buttons
      fontWeight: 700,
    },
  },
  shape: {
    borderRadius: 12, // Smooth rounded edges for buttons/cards
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: "#2B2B2B",
          color: "#FFFFFF",
          borderRadius: "10px",
          padding: "20px",
          boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.4)", // Subtle depth effect
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: "8px",
          fontWeight: "bold",
          padding: "10px 20px",
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: "12px",
          backgroundColor: "#2B2B2B",
          color: "#FFFFFF",
          boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.5)",
        },
      },
    },
  },
});

export const lightTheme = createTheme({
  palette: {
    mode: "light", // Set to dark mode for a casino feel
    primary: {
      main: "#228B22", // Green felt table color
    },
    secondary: {
      main: "#D72638", // Red (inspired by hearts/diamonds)
    },
    background: {
      default: "#F0F0F0", // Light grey background
      paper: "#FFFFFF", // White paper for cards/buttons
    },
    error: {
      main: "#FF4C4C", // Bright red for mistakes
    },
    success: {
      main: "#2ECC71", // Poker chip green for correct actions
    },
    warning: {
      main: "#FFA500", // Orange for caution
    },
    info: {
      main: "#4DA8DA", // Cool blue for information
    },
  },
  typography: {
    fontFamily: `"Play", "Roboto", "Arial", sans-serif`,
    h1: {
      fontFamily: `"Cinzel", "Play", "Roboto", sans-serif`, // Fancy title font
      fontWeight: 700,
      fontSize: "2.5rem",
      color: "#FFD700", // Gold color for key elements
    },
    h2: {
      fontFamily: `"Cinzel", "Roboto", sans-serif`,
      fontWeight: 600,
      fontSize: "2rem",
      color: "#FFFFFF",
    },
    h3: {
      fontWeight: 500,
      fontSize: "1.75rem",
      color: "#C0C0C0",
    },
    body1: {
      fontSize: "1rem",
      fontWeight: 400,
    },
    button: {
      textTransform: "none", // More elegant look for buttons
      fontWeight: 700,
    },
  },
  shape: {
    borderRadius: 12, // Smooth rounded edges for buttons/cards
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: "10px",
          padding: "20px",
          boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.4)", // Subtle depth effect
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: "8px",
          fontWeight: "bold",
          padding: "10px 20px",
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: "12px",
          boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.5)",
        },
      },
    },
  },
});
