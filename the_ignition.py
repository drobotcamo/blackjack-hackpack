import os
import time
from deck import Deck, Card, Suits, Ranks
from typing import List
import sys

NUM_PLAYERS = 5
STARTING_WALLET = 1200
MIN_TIME_STEP = 0.1

HIT = 5001
STAND = 5002
SPLIT = 5003
DOUBLE = 5004

print("BLACKJACK SIMULATOR")

class BetError(Exception):
    """Custom exception for bet-related errors."""
    pass

class BlackjackRules:
    def __init__(
        self,
        dealer_hits_on_soft_17: bool = True,
        blackjack_payout: float = 1.5,
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

class BlackjackHand:
    def __init__(self):
        self.cards: List[Card] = []
        self.is_active = True
        self.active_bet = 0
        self.wallet = STARTING_WALLET
        self.payoutDisplay = 0
        self.busted = False
        self.hasBlackjack = False

        self.split_hands: List[BlackjackHand] = []  # For split hands, if applicable

    def append(self, card: Card):
        self.cards.append(card)
        if self.doesHaveBlackjack():
            self.hasBlackjack = True
        if self.getValue() > 21:
            # if ace, find it and convert it to low ace
            for i, c in enumerate(self.cards):
                if c.rank.name == "A" and c.rank.score_value == 11:
                    self.cards[i].rank = Ranks.LOW_ACE.value
                    break
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
        return f"Hand: {self.cards}, Value: {self.getValue()}, Active Bet: {self.active_bet}, Wallet: {self.wallet}, Bust: {self.bust}, Blackjack: {self.hasBlackjack}"

class BlackjackGame:

    def __init__(self):
        self.deck = Deck()
        self.deck.shuffle()
        self.dealer_hand: BlackjackHand = BlackjackHand()
        self.hands: List[BlackjackHand] = [BlackjackHand() for _ in range(NUM_PLAYERS)]
        self.rules = SouthPointRules

        self.min_bet = 20

        self.marker_index = -1
        self.blackjack_markers = [False for _ in range(NUM_PLAYERS)]
        self.isDrawn = False

        self.input_prompt = ""
        self.prev_input = False
        self.message_content = ""

    def playHand(self):

        while True:
            self.bettingPhase()
            self.initialDealPhase()

            active_hands = [i for i in range(NUM_PLAYERS) if self.hands[i].active_bet > 0]
            for index in active_hands:
                self.playerDecisionPhase(index)

            self.dealerDecisionPhase()

            # payout
            self.makePayouts()

            self.cleanUpRound()


    def makePayouts(self):
        if self.dealer_hand.hasBlackjack:
            for i in range(NUM_PLAYERS):
                if self.hands[i].hasBlackjack:
                    self.hands[i].payoutDisplay = int(self.hands[i].active_bet)
                    self.hands[i].wallet += int(self.hands[i].active_bet)
                else:
                    self.hands[i].active_bet = 0
        elif self.dealer_hand.busted:
            for i in range(NUM_PLAYERS):
                if self.hands[i].busted:
                    self.hands[i].active_bet = 0
                elif self.hands[i].hasBlackjack:
                    self.hands[i].payoutDisplay = int(self.hands[i].active_bet * self.rules.blackjack_payout)
                    self.hands[i].wallet += int(self.hands[i].active_bet * self.rules.blackjack_payout)
                else:
                    self.hands[i].payoutDisplay += int(self.hands[i].active_bet * 2)
                    self.hands[i].wallet += int(self.hands[i].active_bet * 2)
        else:
            for i in range(NUM_PLAYERS):
                if self.hands[i].busted:
                    self.hands[i].active_bet = 0
                elif self.hands[i].hasBlackjack:
                    self.hands[i].payoutDisplay = int(self.hands[i].active_bet * self.rules.blackjack_payout)
                    self.hands[i].wallet += int(self.hands[i].active_bet * self.rules.blackjack_payout)
                elif self.hands[i].getValue() > self.dealer_hand.getValue():
                    self.hands[i].payoutDisplay += int(self.hands[i].active_bet * 2)
                    self.hands[i].wallet += int(self.hands[i].active_bet * 2)
                elif self.hands[i].getValue() == self.dealer_hand.getValue():
                    self.hands[i].payoutDisplay = int(self.hands[i].active_bet)
                    self.hands[i].wallet += int(self.hands[i].active_bet)
                else:
                    self.hands[i].active_bet = 0

        self.drawGame()
        time.sleep(MIN_TIME_STEP * 20)

    def dealerDecisionPhase(self):
        self.dealer_hand.cards[1].flipped = False
        self.drawGame()
        while self.dealer_hand.getValue() < 17 or (self.dealer_hand.getValue() == 17 and self.rules.dealer_hits_on_soft_17 and ([card.rank for card in self.dealer_hand.cards].count(Ranks.ACE.value) > 0)):
            self.dealer_hand.append(self.deck.draw(flipped=False))
            self.drawGame()
            time.sleep(MIN_TIME_STEP)



    def playerDecisionPhase(self, index: int):
        self.setActionMarker(index)

        if self.hands[index].hasBlackjack:
            return

        playerDecision = self.makeDecision(index)

        if playerDecision == HIT:
            self.hands[index].append(self.deck.draw())
            if self.hands[index].busted:
                # player busted
                return
            else:
                self.playerDecisionPhase(index)  # continue decision phase

        elif playerDecision == STAND:
            return

        elif playerDecision == DOUBLE:
            if not self.rules.double_allowed:
                self.message(f"[HAND {index + 1}] Double not allowed.")
                self.playerDecisionPhase(index)

            # check double eligibility
            elif len(self.hands[index].cards) == 2:
                if self.hands[index].active_bet * 2 <= self.hands[index].wallet:
                    self.individualBet(index, self.hands[index].active_bet * 2)
                    self.hands[index].append(self.deck.draw())
                    self.drawGame()
                    time.sleep(MIN_TIME_STEP)
                    self.message(f"[HAND {index + 1}] Doubled bet to ${self.hands[index].active_bet * 2}.")
                    return
            else:
                self.message(f"[HAND {index + 1}] Ineligible for double.")
                self.playerDecisionPhase(index)

        elif playerDecision == SPLIT:
            if not self.rules.split_allowed:
                self.message(f"[HAND {index + 1}] Split not allowed.")
                self.playerDecisionPhase(index)
            elif len(self.hands[index].split_hands) >= self.rules.max_splits:
                self.message(f"[HAND {index + 1}] Maximum splits reached.")
                self.playerDecisionPhase(index)
            # check split eligibility
            elif len(self.hands[index].cards) == 2 and self.hands[index].cards[0].rank == self.hands[index].cards[1].rank:
                # split the hand
                pass
            else:
                # cannot split, notify user
                self.message(f"[HAND {index + 1}] Ineligible for split.")
                self.playerDecisionPhase(index)



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
            if self.hands[i].active_bet > 0:
                self.hands[i].append(self.deck.draw())
                self.drawGame()
                time.sleep(MIN_TIME_STEP)

        self.dealer_hand.append(self.deck.draw(flipped=True))
        self.drawGame()
        time.sleep(MIN_TIME_STEP)

        for i in range(NUM_PLAYERS):
            if self.hands[i].active_bet > 0:
                self.hands[i].append(self.deck.draw())
                if self.hands[i].hasBlackjack:
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
                    self.hands[j].active_bet = self.min_bet
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
        if bet > self.hands[index].wallet:
            raise BetError("Bet exceeds available wallet balance.")
        self.individualBet(index, bet)

    def minBetAll(self, index):
        for i in range(index, NUM_PLAYERS):
            if self.min_bet > self.hands[i].wallet:
                self.hands[i].active_bet = 0
            else:
                self.individualBet(i, self.min_bet)

    def individualBet(self, index: int, bet: int):
        self.hands[index].active_bet = bet
        self.hands[index].wallet -= bet

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

        # Ensure exactly 7 characters
        return result

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

        # fill
        self.symbols = [" " for _ in range(terminal_width * terminal_height)]

        center_x = terminal_width // 2
        for index, card in enumerate(self.dealer_hand.cards):
            x_pos = center_x - 3 + (index * 3)
            reserve = card.ascii_art_coords()
            for item in reserve:
                x = item['x'] + x_pos - 2
                y = item['y']
                if 0 <= x < terminal_width and 0 <= y < terminal_height:
                    self.symbols[x + (y * terminal_width)] = item['symbol']


        spacing = terminal_width // (NUM_PLAYERS + 1)
        for hand_index, hand in enumerate(self.hands):
            for index, card in enumerate(hand.cards):
                x_pos = center_x + (hand_index - NUM_PLAYERS // 2) * spacing + (index * 3)

                reserve = card.ascii_art_coords()
                for item in reserve:
                    x = item['x'] + x_pos - 2
                    y = item['y'] + 4
                    if 0 <= x < terminal_width and 0 <= y < terminal_height:
                        self.symbols[x + (y * terminal_width)] = item['symbol']

        # fill marker
        if self.marker_index != -1:
            marker_x = center_x + (self.marker_index - NUM_PLAYERS // 2) * spacing
            self.symbols[marker_x + (3 * terminal_width)] = "v"

        # fill blackjack markers
        for i, has_blackjack in enumerate(self.blackjack_markers):
            if has_blackjack:
                marker_x = center_x + (i - NUM_PLAYERS // 2) * spacing
                start = marker_x + (3 * terminal_width)
                end = start + 3
                self.symbols[start:end] = "✯★✯"

        #fill bets
        for i in range(NUM_PLAYERS):
            bet_x = center_x + (i - NUM_PLAYERS // 2) * spacing - 3
            bet_y = 7
            if self.hands[i].active_bet == 0:
                bet_str = ""
            else:
                bet_str = self.formatMoneyString(self.hands[i].active_bet) if self.hands[i].payoutDisplay == 0 else self.formatMoneyString(self.hands[i].payoutDisplay, isPayout=True)

            for j, char in enumerate(bet_str):
                if 0 <= bet_x + j < terminal_width:
                    self.symbols[bet_x + j + (bet_y * terminal_width)] = char

        # fill wallets
        for i in range(NUM_PLAYERS):
            wallet_x = center_x + (i - NUM_PLAYERS // 2) * spacing - 3
            wallet_y = 9
            wallet_str = self.formatMoneyString(self.hands[i].wallet)
            self.hands[i].payoutDisplay = 0
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
        for hand in self.hands:
            hand.cards.clear()
            hand.is_active = True
            hand.active_bet = 0
            hand.busted = False
            hand.hasBlackjack = False
            hand.split_hands.clear()
        self.dealer_hand.cards.clear()
        self.marker_index = -1
        self.blackjack_markers = [False for _ in range(NUM_PLAYERS)]
        self.isDrawn = False
        self.input_prompt = ""
        self.prev_input = False
        self.message_content = ""
        self.deck = Deck()
        self.deck.shuffle()
        self.clear_last_n_lines(11)


if __name__ == "__main__":
    game = BlackjackGame()
    game.playHand()

