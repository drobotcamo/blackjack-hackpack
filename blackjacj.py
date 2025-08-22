import os
import time
from deck import Deck, Card, Suits, Ranks
from typing import List
import sys

NUM_PLAYERS = 5
STARTING_WALLET = 1200
BANK_WALLET_ID = -1
MIN_TIME_STEP = 0.1

HIT = 5001
STAND = 5002
SPLIT = 5003
DOUBLE = 5004

split_hand_position_map = {
    2: [-4, 0],
    3: [-6, -3, 1],
    4: [-8, -5, -2, 2]
}


print("BLACKJACK SIMULATOR")

class BetError(Exception):
    """Custom exception for bet-related errors."""
    pass

class BlackjackRules:
    def __init__(
        self,
        dealer_hits_on_soft_17: bool = True,
        blackjack_payout: float = 2.5,
        double_allowed: bool = True,
        double_after_split: bool = True,
        split_allowed: bool = True,
        max_splits: int = 2,
        insurance_allowed: bool = False,
        surrender_allowed: bool = False
    ):
        self.dealer_hits_on_soft_17 = dealer_hits_on_soft_17
        self.blackjack_payout = blackjack_payout
        self.double_allowed = double_allowed
        self.double_after_split = double_after_split
        self.split_allowed = split_allowed
        self.max_splits = max_splits
        self.insurance_allowed = insurance_allowed
        self.surrender_allowed = surrender_allowed

SouthPointRules: BlackjackRules = BlackjackRules()

class Player:
    def __init__(self, id):
        self.id = id
        self.wallet = STARTING_WALLET
        self.hands: List[BlackjackHand] = [BlackjackHand(owner_id=id)]  # Initialize with one hand

class BlackjackHand:
    def __init__(self, owner_id):
        self.cards: List[Card] = []
        self.active_bet = 0
        self.payoutDisplay = 0
        self.busted = False
        self.hasBlackjack = False
        self.canSplit = False
        self.condensed = False  # Fixed typo from 'condesned'
        self.owner_id = owner_id

    def reset(self):
        self.cards: List[Card] = []
        self.active_bet = 0
        self.payoutDisplay = 0
        self.busted = False
        self.hasBlackjack = False
        self.canSplit = False
        self.condensed = False

    def append(self, card: Card):
        self.cards.append(card)
        if self.doesHaveBlackjack():
            self.hasBlackjack = True
        if len(self.cards) == 2 and self.cards[0].rank == self.cards[1].rank:
            self.canSplit = True
        else:
            self.canSplit = False

        # Only convert one high ace to low at a time, as needed
        while self.getValue() > 21 and any(c.rank.name == "A" and c.rank.score_value == 11 for c in self.cards):
            for i, c in enumerate(self.cards):
                if c.rank.name == "A" and c.rank.score_value == 11:
                    # Replace with a new Card object with LOW_ACE rank
                    self.cards[i] = Card(Ranks.LOW_ACE.value, c.suit)
                    break  # Only convert one ace per loop

        if self.getValue() > 21:
            self.busted = True

    def doesHaveBlackjack(self) -> bool:
        if len(self.cards) == 2:
            ranks = [card.rank for card in self.cards]
            return (Ranks.ACE.value in ranks and (Ranks.TEN.value in ranks or Ranks.JACK.value in ranks or Ranks.QUEEN.value in ranks or Ranks.KING.value in ranks))

    def getValue(self) -> int:
        value = 0
        for card in self.cards:
            value += card.rank.score_value
        return value

    def __str__(self):
        return f"Hand: {self.cards}, Value: {self.getValue()}, Active Bet: {self.active_bet}, Bust: {self.busted}, Blackjack: {self.hasBlackjack}"

class BlackjackGame:

    def __init__(self):
        self.deck = Deck()
        self.deck.shuffle()
        self.dealer_hand: BlackjackHand = BlackjackHand(owner_id=0)
        self.dealer_wallet = STARTING_WALLET * 100  # Dealer has separate wallet
        self.players: List[Player] = [Player(i) for i in range(NUM_PLAYERS)]
        self.rules = SouthPointRules

        self.min_bet = 20

        self.marker_index = -1
        self.active_hand_idx = 0
        self.blackjack_markers = [False for _ in range(NUM_PLAYERS)]
        self.isDrawn = False

        self.input_prompt = ""
        self.prev_input = False
        self.message_content = ""

    def playHand(self):
        while True:
            self.drawGame()

            self.bettingPhase()
            self.initialDealPhase()

            active_hands = [i for i in range(NUM_PLAYERS) if self.players[i].hands[0].active_bet > 0]
            for index in active_hands:
                self.playerDecisionPhase(index)

            self.dealerDecisionPhase()

            # payout
            self.makePayouts()
            self.input("Enter for Next Round")

            self.cleanUpRound()

    def makePayment(self, amount: int, from_wallet_id: int, to_wallet_id: int):
        """
        Centralized payment system.
        wallet_id: -1 for dealer, 0-4 for players
        """
        if from_wallet_id == BANK_WALLET_ID:  # From dealer
            if self.dealer_wallet >= amount:
                self.dealer_wallet -= amount
                if to_wallet_id >= 0:  # To player
                    self.players[to_wallet_id].wallet += amount
            else:
                raise ValueError(f"Dealer insufficient funds: {self.dealer_wallet} < {amount}")
        elif to_wallet_id == BANK_WALLET_ID:  # To dealer
            if from_wallet_id >= 0:  # From player
                if self.players[from_wallet_id].wallet >= amount:
                    self.players[from_wallet_id].wallet -= amount
                    self.dealer_wallet += amount
                else:
                    raise ValueError(f"Player {from_wallet_id} insufficient funds: {self.players[from_wallet_id].wallet} < {amount}")
        elif from_wallet_id >= 0 and to_wallet_id >= 0:  # Player to player
            if self.players[from_wallet_id].wallet >= amount:
                self.players[from_wallet_id].wallet -= amount
                self.players[to_wallet_id].wallet += amount
            else:
                raise ValueError(f"Player {from_wallet_id} insufficient funds: {self.players[from_wallet_id].wallet} < {amount}")
        else:
            raise ValueError(f"Invalid wallet IDs: from={from_wallet_id}, to={to_wallet_id}")

    def makePayouts(self):
        if self.dealer_hand.hasBlackjack:
            for i in range(NUM_PLAYERS):
                for hand in self.players[i].hands:
                    if hand.hasBlackjack:
                        hand.payoutDisplay = int(hand.active_bet)
                        self.makePayment(hand.active_bet, BANK_WALLET_ID, i)
                    # Losing bets already taken during betting phase
        elif self.dealer_hand.busted:
            for i in range(NUM_PLAYERS):
                for hand in self.players[i].hands:
                    if hand.busted:
                        # Losing bets already taken during betting phase
                        pass
                    elif hand.hasBlackjack:
                        payout = int(hand.active_bet * self.rules.blackjack_payout)
                        hand.payoutDisplay = payout
                        self.makePayment(payout, BANK_WALLET_ID, i)
                    else:
                        payout = int(hand.active_bet * 2)
                        hand.payoutDisplay = payout
                        self.makePayment(payout, BANK_WALLET_ID, i)
        else:
            for i in range(NUM_PLAYERS):
                for hand in self.players[i].hands:
                    if hand.busted:
                        # Losing bets already taken during betting phase
                        pass
                    elif hand.hasBlackjack:
                        payout = int(hand.active_bet * self.rules.blackjack_payout)
                        hand.payoutDisplay = payout
                        self.makePayment(payout, BANK_WALLET_ID, i)
                    elif hand.getValue() > self.dealer_hand.getValue():
                        payout = int(hand.active_bet * 2)
                        hand.payoutDisplay = payout
                        self.makePayment(payout, BANK_WALLET_ID, i)
                    elif hand.getValue() == self.dealer_hand.getValue():
                        # Push - return bet
                        hand.payoutDisplay = int(hand.active_bet)
                        self.makePayment(hand.active_bet, BANK_WALLET_ID, i)
                    # Losing bets already taken during betting phase

    def dealerDecisionPhase(self):
        self.dealer_hand.cards[1].flipped = False
        self.drawGame()
        while self.dealer_hand.getValue() < 17 or (self.dealer_hand.getValue() == 17 and self.rules.dealer_hits_on_soft_17 and ([card.rank for card in self.dealer_hand.cards].count(Ranks.ACE.value) > 0)):
            self.dealer_hand.append(self.deck.draw(flipped=False))
            self.drawGame()
            time.sleep(MIN_TIME_STEP)

    def playerDecisionPhase(self, index: int):
        hand_idx = 0
        while hand_idx < len(self.players[index].hands):
            hand = self.players[index].hands[hand_idx]
            self.setActionMarker(index)
            self.active_hand_idx = hand_idx

            if hand.hasBlackjack:
                # Condense the hand immediately
                hand.condensed = True
                hand_idx += 1
                continue

            playerDecision = self.makeDecision(index)

            if playerDecision == HIT:
                hand.append(self.deck.draw())
                if hand.busted:
                    # Condense the hand when busted
                    hand.condensed = True
                    hand_idx += 1
                    continue
                # Stay on same hand for further decisions

            elif playerDecision == STAND:
                # Condense the hand when standing
                hand.condensed = True
                hand_idx += 1

            elif playerDecision == DOUBLE:
                if not self.rules.double_allowed:
                    self.message(f"[HAND {index + 1}] Double not allowed.")
                    continue
                elif len(hand.cards) == 2:
                    if hand.active_bet <= self.players[index].wallet:
                        # Take additional bet from player wallet
                        self.makePayment(hand.active_bet, index, BANK_WALLET_ID)
                        hand.active_bet *= 2
                        hand.append(self.deck.draw())
                        self.drawGame()
                        time.sleep(MIN_TIME_STEP)
                        self.message(f"[HAND {index + 1}] Doubled bet to ${hand.active_bet}.")
                        # Condense the hand after doubling
                        hand.condensed = True
                        hand_idx += 1
                    else:
                        self.message(f"[HAND {index + 1}] Ineligible for double.")
                else:
                    self.message(f"[HAND {index + 1}] Ineligible for double.")

            elif playerDecision == SPLIT:
                if not self.rules.split_allowed:
                    self.message(f"[HAND {index + 1}] Split not allowed.")
                    continue
                elif len(self.players[index].hands) >= self.rules.max_splits + 1:
                    self.message(f"[HAND {index + 1}] Maximum splits reached.")
                    continue
                elif hand.canSplit:
                    split_bet = hand.active_bet
                    if self.players[index].wallet >= split_bet:
                        # Take bet for second hand
                        self.makePayment(split_bet, index, BANK_WALLET_ID)

                        card1, card2 = hand.cards
                        new_hand1 = BlackjackHand(owner_id=self.players[index].id)
                        new_hand2 = BlackjackHand(owner_id=self.players[index].id)
                        new_hand1.append(Card(Ranks.ACE.value if card1.rank == Ranks.LOW_ACE.value else card1.rank, card1.suit))
                        new_hand2.append(Card(Ranks.ACE.value if card2.rank == Ranks.LOW_ACE.value else card2.rank, card2.suit))
                        new_hand1.active_bet = split_bet
                        new_hand2.active_bet = split_bet

                        # Remove the original hand and insert the new hands at its position
                        self.players[index].hands.pop(hand_idx)
                        self.players[index].hands.insert(hand_idx, new_hand2)
                        self.players[index].hands.insert(hand_idx, new_hand1)
                        # Do not increment hand_idx, so the next iteration will process the first new split hand
                    else:
                        self.message(f"[HAND {index + 1}] Not enough funds to split.")
                        continue
                else:
                    self.message(f"[HAND {index + 1}] Ineligible for split.")
                    # Still condense invalid split attempts
                    hand.condensed = True
                    hand_idx += 1

    def setBlackjackMarker(self, index: int):
        self.blackjack_markers[index] = True

    def makeDecision(self, index: int) -> bool:
        decisionInput = self.input(f"[HAND {index + 1}]  enter for stand, H for hit").lower()

        if decisionInput == "h":
            return HIT
        elif decisionInput == "d":
            return DOUBLE
        elif decisionInput == "s":
            return SPLIT
        elif decisionInput == "":
             return STAND
        else:
            # invalid input, try again
            self.message(f"[HAND {index + 1}] Invalid Input - enter for stand, H for hit")
            return self.makeDecision(index)

    def bettingPhase(self):
        for i in range(NUM_PLAYERS):
            end = self.individualBetPhase(i)
            if end:
                break

    def initialDealPhase(self):
        self.dealer_hand.append(self.deck.draw())
        self.drawGame()
        time.sleep(MIN_TIME_STEP)

        for i in range(NUM_PLAYERS):
            if self.players[i].hands[0].active_bet > 0:
                self.players[i].hands[0].append(self.deck.draw())
                self.drawGame()
                time.sleep(MIN_TIME_STEP)

        self.dealer_hand.append(self.deck.draw(flipped=True))
        self.drawGame()
        time.sleep(MIN_TIME_STEP)

        for i in range(NUM_PLAYERS):
            if self.players[i].hands[0].active_bet > 0:
                self.players[i].hands[0].append(self.deck.draw())
                if self.players[i].hands[0].hasBlackjack:
                    # self.payoutBlackjack(i)
                    self.setBlackjackMarker(i)
                self.drawGame()
                time.sleep(MIN_TIME_STEP)

    def individualBetPhase(self, index):
        unproccessed_input = self.input(f"Place bet for hand {index + 1} ('enter' for min ${self.min_bet} all): $")

        # bet all min
        if unproccessed_input == "":
            self.minBetAll(index)
            return True

        # set new min
        if unproccessed_input[-1] == "m":
            try:
                self.min_bet = int(unproccessed_input[:-1])
                for j in range(NUM_PLAYERS):
                    self.players[j].hands[0].active_bet = self.min_bet
            except ValueError:
                self.message("Invalid minimum bet format. Must be a whole number")
                self.individualBetPhase(index)  # retry if not valid
            except BetError as e:
                self.message(str(e))
                self.individualBetPhase(index)  # retry if not valid

        # place individual bet
        else:
            try:
                bet = int(unproccessed_input)
                self.requestBet(index, bet)
            except ValueError:
                self.message("Invalid minimum bet format. Must be a number")
                self.individualBetPhase(index)  # retry if not valid
            except BetError as e:
                self.message(str(e))
                self.individualBetPhase(index)  # retry if not valid

    def setActionMarker(self, index: int):
        self.marker_index = index

    def requestBet(self, index: int, bet: int):
        if bet != 0 and bet < self.min_bet:
            raise BetError("Bet must be at least the minimum bet.")
        if bet > self.players[index].wallet:
            raise BetError("Bet exceeds available wallet balance.")
        self.individualBet(index, bet)

    def minBetAll(self, index):
        for i in range(index, NUM_PLAYERS):
            if self.min_bet > self.players[i].wallet:
                self.players[i].hands[0].active_bet = 0
            else:
                self.individualBet(i, self.min_bet)

    def individualBet(self, index: int, bet: int):
        if bet > 0:
            # Take bet from player wallet to dealer/bank
            self.makePayment(bet, index, BANK_WALLET_ID)
        self.players[index].hands[0].active_bet = bet

    def input(self, prompt: str) -> str:
        self.input_prompt = prompt
        return self.drawGame(input_request=prompt)

    def message(self, content: str):
        self.message_content = content

    def formatMoneyString(self, value: int, isPayout=False) -> str:
        # Returns a 7-character payout string with custom formatting.
        negative = value < 0
        abs_value = abs(value)
        if abs_value >= 1_000_000_000:
            # Billions
            num = abs_value / 1_000_000_000
            num_str = f"{num:.2f}b" if num < 10 else f"{num:.1f}b"
        elif abs_value >= 1_000_000:
            # Millions
            num = abs_value / 1_000_000
            num_str = f"{num:.2f}M" if num < 10 else f"{num:.1f}M"
        elif abs_value >= 1_000:
            # Thousands
            num = abs_value / 1_000
            num_str = f"{num:.2f}k" if num < 10 else f"{num:.1f}k"
        else:
            num_str = str(abs_value)

        if isPayout:
            # Format: " $123 "
            return f"+(${num_str})".center(8)
        if negative:
            # Format: " -$123 "
            return f"{"-$"+num_str}".center(7)
        else:
            # Format: " ${123} "
            return f"{"$"+num_str}".center(7)

    def clear_last_n_lines(self, n=3):
            for _ in range(n):
                # Move cursor up one line
                sys.stdout.write('\x1b[1A')
                # Clear the line
                sys.stdout.write('\x1b[2K')
            sys.stdout.flush()

    def drawGame(self, input_request="") -> str | None:
        terminal_width = os.get_terminal_size().columns
        terminal_height = 10

        if(self.isDrawn):
            self.clear_last_n_lines(terminal_height + (1 if self.prev_input else 0) + 1)
            self.prev_input = False
            self.prev_message = False
        else:
            self.isDrawn = True

        self.symbols = [" " for _ in range(terminal_width * terminal_height)]
        center_x = terminal_width // 2

        # Draw dealer cards
        for index, card in enumerate(self.dealer_hand.cards):
            x_pos = center_x - 3 + (index * 3)
            reserve = card.ascii_art_coords()
            for item in reserve:
                x = item['x'] + x_pos - 2
                y = item['y']
                if 0 <= x < terminal_width and 0 <= y < terminal_height:
                    self.symbols[x + (y * terminal_width)] = item['symbol']

        spacing = terminal_width // (NUM_PLAYERS + 1)
        # Track marker position for split hands
        marker_x = None
        marker_y = None

        for player_index, player in enumerate(self.players):
            if len(player.hands) == 1:
                hand = player.hands[0]
                for index, card in enumerate(hand.cards):
                    x_pos = center_x + (player_index - NUM_PLAYERS // 2) * spacing + (index * 3)
                    reserve = card.ascii_art_coords()
                    for item in reserve:
                        x = item['x'] + x_pos - 2
                        y = item['y'] + 4
                        if 0 <= x < terminal_width and 0 <= y < terminal_height:
                            self.symbols[x + (y * terminal_width)] = item['symbol']
                # Marker for single hand
                if self.marker_index == player_index:
                    marker_x = center_x + (player_index - NUM_PLAYERS // 2) * spacing
                    marker_y = 3
            else:
                hand_x_positions = []
                for hand_index, hand in enumerate(player.hands):
                    if hand_index == 0:
                        x_pos = center_x + (player_index - NUM_PLAYERS // 2) * spacing + split_hand_position_map[len(player.hands)][hand_index]
                    else:
                        prev_hand = player.hands[hand_index - 1]
                        prev_x = hand_x_positions[hand_index - 1]
                        if prev_hand.condensed:  # Fixed typo
                            x_pos = prev_x + 5
                        else:
                            x_pos = prev_x + (len(prev_hand.cards) * 3) + 2
                    hand_x_positions.append(x_pos)

                    if hand.condensed:  # Fixed typo
                        reserve = Card(Ranks.ACE.value, Suits.DIAMONDS.value, handValue=hand.getValue()).ascii_art_coords()
                        for item in reserve:
                            x = item['x'] + x_pos - 2
                            y = item['y'] + 4
                            if 0 <= x < terminal_width and 0 <= y < terminal_height:
                                self.symbols[x + (y * terminal_width)] = item['symbol']
                        if hand.hasBlackjack:
                            bj_x = x_pos
                            start = bj_x + (3 * terminal_width)
                            end = start + 3
                            self.symbols[start:end] = "✯★✯"
                    else:
                        for card_index, card in enumerate(hand.cards):
                            card_x_pos = x_pos + (card_index * 3)
                            reserve = card.ascii_art_coords()
                            for item in reserve:
                                x = item['x'] + card_x_pos - 2
                                y = item['y'] + 4
                                if 0 <= x < terminal_width and 0 <= y < terminal_height:
                                    self.symbols[x + (y * terminal_width)] = item['symbol']

                # Marker for split hands
                if self.marker_index == player_index:
                    marker_x = hand_x_positions[self.active_hand_idx]
                    marker_y = 3

                # Blackjack markers for split hands
                for hand_index, hand in enumerate(player.hands):
                    if hand.hasBlackjack and not hand.condensed:  # Only show stars if not condensed
                        bj_x = hand_x_positions[hand_index]
                        start = bj_x + (3 * terminal_width)
                        end = start + 3
                        self.symbols[start:end] = "✯★✯"

        # Draw marker
        if marker_x is not None and marker_y is not None:
            self.symbols[marker_x + (marker_y * terminal_width)] = "v"

        # Fill bets - sum all hands for a player
        for i in range(NUM_PLAYERS):
            bet_x = center_x + (i - NUM_PLAYERS // 2) * spacing - 3
            bet_y = 7
            total_bet = sum(hand.active_bet for hand in self.players[i].hands)
            total_payout = sum(hand.payoutDisplay for hand in self.players[i].hands)

            if total_bet == 0:
                bet_str = ""
            else:
                bet_str = self.formatMoneyString(total_bet) if total_payout == 0 else self.formatMoneyString(total_payout, isPayout=True)

            for j, char in enumerate(bet_str):
                if 0 <= bet_x + j < terminal_width:
                    self.symbols[bet_x + j + (bet_y * terminal_width)] = char

        # fill wallets
        for i in range(NUM_PLAYERS):
            wallet_x = center_x + (i - NUM_PLAYERS // 2) * spacing - 3
            wallet_y = 9
            wallet_str = self.formatMoneyString(self.players[i].wallet)
            # Clear payout displays after showing
            for hand in self.players[i].hands:
                hand.payoutDisplay = 0
            for j, char in enumerate(wallet_str):
                if 0 <= wallet_x + j < terminal_width:
                    self.symbols[wallet_x + j + (wallet_y * terminal_width)] = char

        # draw border
        padding = terminal_width // 10
        for x in range(padding, terminal_width - padding):
            self.symbols[8*terminal_width + x] = "─"
            self.symbols[8*terminal_width + padding] = "┌"
            self.symbols[8*terminal_width + terminal_width - padding] = "┐"
        self.symbols[9*terminal_width + padding] = "│"
        self.symbols[9*terminal_width + terminal_width - padding] = "│"

        # draw
        for y in range(terminal_height):
            for x in range(terminal_width):
                print(self.symbols[x+(y*terminal_width)], end="")
            print("")

        print(self.message_content)
        self.message_content = ""

        # input
        if input_request != "":
            self.prev_input = True
            return input(self.input_prompt)

    def cleanUpRound(self):
        for player in self.players:
            player.hands.clear()
            player.hands.append(BlackjackHand(owner_id=player.id))
        self.dealer_hand.reset()
        self.marker_index = -1
        self.blackjack_markers = [False for _ in range(NUM_PLAYERS)]
        self.message_content = ""
        self.deck = Deck()
        self.deck.shuffle()


if __name__ == "__main__":
    game = BlackjackGame()
    game.playHand()
