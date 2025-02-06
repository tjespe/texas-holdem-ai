import { ArrowDropDown } from "@mui/icons-material";
import { Button, ButtonGroup, Menu, MenuItem } from "@mui/material";
import { useState } from "react";

const botOptions = [
  { label: "Default", value: "max_ev_and_mocker" },
  { label: "Advanced (slower)", value: "max_ev" },
  { label: "Random", value: "random" },
];

export type BotType = (typeof botOptions)[number]["value"];

interface Props {
  onAddBot: (type: BotType) => void;
}

export function AddBotButton({ onAddBot }: Props) {
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [defaultBotType, setDefaultBotType] = useState<BotType>("max_ev"); // Default bot type

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setMenuAnchor(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
  };

  const handleSelectBot = (type: BotType) => {
    console.log("Selected", type);

    setDefaultBotType(type);
    onAddBot(type);
    handleMenuClose();
  };

  return (
    <div>
      <ButtonGroup variant="outlined">
        {/* Main "Add Bot" button (adds the currently selected bot) */}
        <Button onClick={() => onAddBot(defaultBotType)}>Add Bot</Button>

        {/* Dropdown button */}
        <Button onClick={handleMenuOpen} size="small" style={{ padding: 0 }}>
          <ArrowDropDown />
        </Button>
      </ButtonGroup>

      {/* Dropdown menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        {botOptions.map((bot) => (
          <MenuItem key={bot.value} onClick={() => handleSelectBot(bot.value)}>
            {bot.label}
          </MenuItem>
        ))}
      </Menu>
    </div>
  );
}
