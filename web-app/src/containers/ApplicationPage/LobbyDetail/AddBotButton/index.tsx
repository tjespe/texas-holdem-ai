import { ArrowDropDown } from "@mui/icons-material";
import { Button, ButtonGroup, Menu, MenuItem } from "@mui/material";
import { useEffect, useState } from "react";
import { BotOption, listBotOptions } from "../../../../api/lobbies";
import { randomNames } from "./names";

interface Props {
  onAddBot: (bot: BotOption) => void;
}

export function AddBotButton({ onAddBot }: Props) {
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [botOptions, setBotOptions] = useState<BotOption[]>();

  useEffect(function fetchBotOptions() {
    listBotOptions().then((options) => {
      setBotOptions(options);
    });
  }, []);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setMenuAnchor(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
  };

  const handleSelectBot = (opt: BotOption | "default") => {
    console.log("Selected", opt);

    onAddBot(
      opt === "default"
        ? {
            type: "MaxEVandHumanMocker",
            name: randomNames[Math.floor(Math.random() * randomNames.length)],
          }
        : opt
    );
    handleMenuClose();
  };

  return (
    <div>
      <ButtonGroup variant="outlined">
        {/* Main "Add Bot" button (adds the currently selected bot) */}
        <Button onClick={() => handleSelectBot("default")}>Add Bot</Button>

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
        {botOptions?.map((bot) => (
          <MenuItem key={bot.type} onClick={() => handleSelectBot(bot)}>
            {bot.name}
          </MenuItem>
        )) ?? <MenuItem disabled>Loading...</MenuItem>}
      </Menu>
    </div>
  );
}
