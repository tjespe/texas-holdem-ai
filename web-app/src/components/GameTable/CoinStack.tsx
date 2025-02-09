import { Paid } from "@mui/icons-material";
import { Box, Stack, Typography } from "@mui/material";
import { ComponentProps } from "react";

interface Props extends ComponentProps<typeof Stack> {
  chips: number;
  large?: boolean;
}

export const CoinStack: React.FC<Props> = ({
  chips,
  large = false,
  ...props
}) => {
  const iconFontSize = large ? "medium" : "small";
  return (
    <Stack
      direction="row"
      alignItems="center"
      width="fit-content"
      margin="auto"
      {...props}
    >
      <Stack direction="column" spacing={-1}>
        <Stack direction="row" spacing={-1}>
          <Paid fontSize={iconFontSize} />
          <Paid fontSize={iconFontSize} />
        </Stack>
        <Box>
          <Paid fontSize={iconFontSize} />
        </Box>
      </Stack>
      <Typography variant={large ? "h4" : "subtitle1"} fontWeight={500}>
        {chips}
      </Typography>
    </Stack>
  );
};
