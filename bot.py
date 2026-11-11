
# -------------------------
# MINES GAME
# -------------------------

@bot.tree.command(name="mines", description="Play Mines 5x5")
@app_commands.describe(
    bet="Your bet",
    bombs="Number of bombs (1-24)"
)
async def mines(
    interaction: discord.Interaction,
    bet: int,
    bombs: app_commands.Range[int, 1, 24]
):
    if not valid_bet(interaction.user.id, bet):
        await interaction.response.send_message(
            "❌ Invalid bet or insufficient balance!",
            ephemeral=True
        )
        return

    remove_money(interaction.user.id, bet)

    board = ["💎"] * (25 - bombs) + ["💣"] * bombs
    random.shuffle(board)

    revealed = set()
    game_over = False
    multiplier = 1.0

    class MinesView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=180)

            for i in range(25):
                button = discord.ui.Button(
                    label="?",
                    style=discord.ButtonStyle.secondary,
                    row=i // 5
                )
                button.callback = self.make_callback(i)
                self.add_item(button)

            self.cashout = discord.ui.Button(
                label="CASHOUT",
                style=discord.ButtonStyle.success,
                row=4
            )
            self.cashout.callback = self.cashout_callback
            self.add_item(self.cashout)

        def update_buttons(self):
            for i, button in enumerate(
                [b for b in self.children if b is not self.cashout]
            ):
                if i in revealed:
                    button.label = "💎" if board[i] == "💎" else "💣"
                    button.disabled = True

            self.cashout.disabled = len(revealed) == 0

        def make_callback(self, index):
            async def callback(interaction2):
                nonlocal game_over, multiplier

                if interaction2.user.id != interaction.user.id:
                    await interaction2.response.send_message(
                        "❌ This is not your game!",
                        ephemeral=True
                    )
                    return

                if game_over or index in revealed:
                    await interaction2.response.send_message(
                        "Invalid move!",
                        ephemeral=True
                    )
                    return

                revealed.add(index)

                if board[index] == "💣":
                    game_over = True
                    self.update_buttons()

                    for i, button in enumerate(
                        [b for b in self.children if b is not self.cashout]
                    ):
                        button.label = board[i]
                        button.disabled = True

                    self.cashout.disabled = True

                    await interaction2.response.edit_message(
                        content="💥 **BOOM! You hit a mine!**\n"
                                f"Lost: {bet}$",
                        view=self
                    )
                    self.stop()
                    return

                safe_count = len(revealed)
                multiplier = (
                    (1 - bombs / 25) /
                    (1 - bombs / 25 - safe_count / 25 + safe_count / 25)
                ) if False else 1 + safe_count * bombs * 0.035

                self.update_buttons()

                await interaction2.response.edit_message(
                    content=(
                        f"💎 **MINES**\n"
                        f"Safe tiles: {safe_count}\n"
                        f"Multiplier: x{multiplier:.2f}\n"
                        f"Potential payout: {int(bet * multiplier)}$"
                    ),
                    view=self
                )

            return callback

        async def cashout_callback(self, interaction2):
            nonlocal game_over

            if interaction2.user.id != interaction.user.id:
                await interaction2.response.send_message(
                    "❌ Not your game!", ephemeral=True
                )
                return

            if game_over or len(revealed) == 0:
                await interaction2.response.send_message(
                    "Reveal a diamond first!", ephemeral=True
                )
                return

            game_over = True
            winnings = int(bet * multiplier)
            add_money(interaction.user.id, winnings)

            self.update_buttons()

            for button in self.children:
                button.disabled = True

            await interaction2.response.edit_message(
                content=(
                    f"💰 **CASHOUT SUCCESSFUL!**\n"
                    f"Multiplier: x{multiplier:.2f}\n"
                    f"You received: **{winnings}$**"
                ),
                view=self
            )
            self.stop()

    view = MinesView()

    await interaction.response.send_message(
        f"💣 **MINES 5x5**\n"
        f"Bet: {bet}$\n"
        f"Bombs: {bombs}\n"
        f"Find diamonds and cash out!",
        view=view
    )
