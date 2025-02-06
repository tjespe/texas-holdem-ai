import { Box, Link, Stack } from "@mui/material";
import { Breadcrumbs } from "../../components/BreadCrumbs";
import { useAuthContext } from "../../contexts/AuthContext";
import { Outlet, Link as RouterLink } from "react-router-dom";

export function ApplicationPage() {
  const { logOut } = useAuthContext();

  return (
    <Box height="100vh">
      <Stack direction="row" justifyContent="space-between" padding={2}>
        <Breadcrumbs />
        <Link
          component={RouterLink}
          to="/"
          onClick={logOut}
          sx={{
            fontWeight: "bold",
            textDecoration: "none",
            "&:hover": { textDecoration: "underline" },
          }}
        >
          Log out
        </Link>
      </Stack>
      <Outlet />
    </Box>
  );
}
