import { Breadcrumbs as MuiBreadcrumbs, Link, Typography } from "@mui/material";
import { Link as RouterLink, useLocation } from "react-router-dom";

const toCapitalCase = (str: string) =>
  str.charAt(0).toUpperCase() + str.slice(1);

export function Breadcrumbs() {
  const location = useLocation(); // Get current path
  const pathnames = location.pathname.split("/").filter((x) => x);

  return (
    <MuiBreadcrumbs aria-label="breadcrumb">
      <Link
        component={RouterLink}
        to="/"
        sx={{
          fontWeight: "bold",
          textDecoration: "none",
          "&:hover": { textDecoration: "underline" },
        }}
      >
        Home
      </Link>
      {pathnames.map((name, index) => {
        const routeTo = `/${pathnames.slice(0, index + 1).join("/")}`;
        const isLast = index === pathnames.length - 1;
        const label = toCapitalCase(decodeURIComponent(name));

        return isLast ? (
          <Typography key={routeTo}>{label}</Typography>
        ) : (
          <Link
            key={routeTo}
            component={RouterLink}
            to={routeTo}
            sx={{
              fontWeight: "bold",
              textDecoration: "none",
              "&:hover": { textDecoration: "underline" },
            }}
          >
            {label}
          </Link>
        );
      })}
    </MuiBreadcrumbs>
  );
}
