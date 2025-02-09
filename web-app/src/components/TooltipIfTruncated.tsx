import { Tooltip } from "@mui/material";
import React, { ComponentProps, useState } from "react";

interface Props
  extends Omit<ComponentProps<typeof Tooltip>, "children" | "title"> {
  children: string;
}

export const TooltipIfTruncated: React.FC<Props> = ({
  children: child,
  ...props
}) => {
  const [ref, setRef] = useState<HTMLElement | null>(null);
  const scrollWidth = ref?.parentElement?.scrollWidth || 0;
  const clientWidth = ref?.parentElement?.clientWidth || 0;
  const isTruncated = scrollWidth > clientWidth;

  return (
    <Tooltip title={isTruncated ? child : undefined} {...props}>
      <span ref={setRef}>{child}</span>
    </Tooltip>
  );
};
